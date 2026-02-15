import argparse
import logging
from pathlib import Path
from time import sleep

from tqdm import tqdm

from .logging import setup_logging
from .remove_ads import remove_ads

logger = logging.getLogger(__name__)


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

    for fn in tqdm(queue, desc="Podcasts to process"):
        remove_ads(
            file_name=str(fn),
            overwrite=overwrite,
            model=model,
        )

def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Remove ads from a podcast episode.",
    )
    parser.add_argument(
        "--directory", default=".", help="Path to the podcast directory.",
    )
    parser.add_argument(
        "--sleep", type=int, default=600, help="Sleep time in seconds between processing runs.",
    )
    parser.add_argument(
        "--model", default=None, help="OpenAI model to use for ad classification.",
    )
    args = parser.parse_args()

    while True:
        try:
            walk_directory(args.directory, model=args.model)
            logger.info("Sleeping for %d minutes", args.sleep // 60)
            sleep(args.sleep)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
