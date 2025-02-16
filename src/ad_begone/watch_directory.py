from pathlib import Path
from time import sleep

from .remove_ads import remove_ads


def walk_directory(directory: str):
    for path in Path(directory).rglob("*.mp3"):
        remove_ads(
            file_name=str(path),
            overwrite=False,
    )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Remove ads from a podcast episode.")
    parser.add_argument(
        "directory",
        type=str,
        help="Path to the podcast episode file.",
        default=".",
    )
    parser.add_argument(
        "sleep",
        type=int,
        help="Sleep time between each file",
        default=600,
    )
    args = parser.parse_args()

    while True:
        try:
            walk_directory(args.directory)
            sleep(args.sleep)
        except KeyboardInterrupt:
            break
