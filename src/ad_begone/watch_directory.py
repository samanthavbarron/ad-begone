import argparse
from pathlib import Path
from time import sleep

from tqdm import tqdm

from .remove_ads import remove_ads


def walk_directory(
    directory: str,
    overwrite: bool = False,
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
        )

def main():
    parser = argparse.ArgumentParser(description="Remove ads from a podcast episode.")
    parser.add_argument(
        "--directory",
        type=str,
        help="Path to the podcast episode file.",
        default=".",
    )
    parser.add_argument(
        "--sleep",
        type=int,
        help="Sleep time between each file",
        default=600,
    )
    args = parser.parse_args()

    while True:
        try:
            walk_directory(args.directory)
            print(f"Sleeping for {int(args.sleep / 60)} minutes...")
            sleep(args.sleep)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
