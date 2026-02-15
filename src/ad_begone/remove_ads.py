import logging
import time
from pathlib import Path

from .ad_trimmer import AdTrimmer
from .utils import join_files, split_file

from .notif_path import NOTIF_PATH

logger = logging.getLogger(__name__)

def remove_ads(
    file_name: str,
    out_name: str | None = None,
    notif_name: str = NOTIF_PATH,
    overwrite: bool = False,
    model: str | None = None,
):
    if out_name is None:
        out_name = file_name

    path = Path(file_name)
    path_file_hit = path.parent / f".hit.{path.name}.txt"

    if path_file_hit.exists() and not overwrite:
        logger.debug("Already processed %s, skipping", file_name)
        return

    logger.info("Removing ads from %s", file_name)
    start_time = time.monotonic()

    split_names = split_file(file_name)
    for i, split_name in enumerate(split_names, 1):
        logger.info("Processing part %d/%d for %s", i, len(split_names), file_name)
        trimmer = AdTrimmer(split_name, model=model)
        trimmer.remove_ads(notif_name=notif_name)
    logger.info("Joining parts for %s", file_name)
    join_files(file_name)

    elapsed = time.monotonic() - start_time
    minutes, seconds = divmod(elapsed, 60)
    logger.info("Done processing %s (elapsed: %dm %ds)", file_name, int(minutes), int(seconds))
    path_file_hit.write_text("")

if __name__ == "__main__":
    from typing import Optional

    import pydantic.v1 as pydantic
    import pydantic_argparse

    class RemoveAdsArgs(pydantic.BaseModel):
        file_name: str = pydantic.Field(
            description="Path to the podcast episode file.",
        )
        out_name: Optional[str] = pydantic.Field(
            default=None,
            description="Path to save the podcast episode file without ads.",
        )
        model: Optional[str] = pydantic.Field(
            default=None,
            description="OpenAI model to use for ad classification.",
        )

    parser = pydantic_argparse.ArgumentParser(
        model=RemoveAdsArgs,
        description="Remove ads from a podcast episode.",
    )
    args = parser.parse_typed_args()

    remove_ads(args.file_name, args.out_name, model=args.model)
