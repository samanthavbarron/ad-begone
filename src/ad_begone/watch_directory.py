import logging
from pathlib import Path
from time import sleep

from typing import Optional

import pydantic.v1 as pydantic
import pydantic_argparse

from .logging import setup_logging
from .remove_ads import remove_ads

logger = logging.getLogger(__name__)


class WatchArgs(pydantic.BaseModel):
    directory: str = pydantic.Field(
        default=".",
        description="Path to the podcast directory.",
    )
    sleep: int = pydantic.Field(
        default=600,
        gt=0,
        description="Sleep time in seconds between processing runs.",
    )
    model: Optional[str] = pydantic.Field(
        default=None,
        description="OpenAI model to use for ad classification.",
    )


def walk_directory(
    directory: str,
    overwrite: bool = False,
    model: str | None = None,
):
    queue = []
    for fn in Path(directory).rglob("*.mp3"):
        path = Path(fn)
        path_file_hit = path.parent / f".hit.{path.name}.txt"
        if path_file_hit.exists() and not overwrite:
            continue
        queue.append(fn)

    logger.info("Found %d podcast(s) to process", len(queue))
    for i, fn in enumerate(queue, 1):
        logger.info("Processing podcast %d/%d: %s", i, len(queue), fn)
        remove_ads(
            file_name=str(fn),
            overwrite=overwrite,
            model=model,
        )

def main():
    setup_logging()

    parser = pydantic_argparse.ArgumentParser(
        model=WatchArgs,
        description="Remove ads from a podcast episode.",
    )
    args = parser.parse_typed_args()

    while True:
        try:
            walk_directory(args.directory, model=args.model)
            logger.info("Sleeping for %d minutes", args.sleep // 60)
            sleep(args.sleep)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
