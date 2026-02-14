from pathlib import Path
from time import sleep

import pydantic.v1 as pydantic
import pydantic_argparse
from tqdm import tqdm

from .remove_ads import remove_ads


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
    parser = pydantic_argparse.ArgumentParser(
        model=WatchArgs,
        description="Remove ads from a podcast episode.",
    )
    args = parser.parse_typed_args()

    while True:
        try:
            walk_directory(args.directory)
            print(f"Sleeping for {int(args.sleep / 60)} minutes...")
            sleep(args.sleep)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
