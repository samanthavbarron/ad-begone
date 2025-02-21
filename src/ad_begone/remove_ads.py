from pathlib import Path
from tqdm import tqdm

from .ad_trimmer import AdTrimmer
from .utils import join_files, split_file

from .notif_path import NOTIF_PATH

def remove_ads(
    file_name: str,
    out_name: str | None = None,
    notif_name: str = NOTIF_PATH,
    overwrite: bool = False,
):
    if out_name is None:
        out_name = file_name
    
    path = Path(file_name)
    path_file_hit = path.parent / f".hit.{path.name}.txt"

    if path_file_hit.exists() and not overwrite:
        print("Already hit")
        return
    
    print(f"Removing ads from {file_name}")
    
    split_names = split_file(file_name)
    for split_name in tqdm(split_names, desc="Splitting parts"):
        trimmer = AdTrimmer(split_name)
        trimmer.remove_ads(notif_name=notif_name)
    print("Joining parts")
    join_files(file_name)
    print("Done")
    path_file_hit.write_text("")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Remove ads from a podcast episode.")

    parser.add_argument("file_name", type=str, help="Path to the podcast episode file.")

    parser.add_argument(
        "--out_name",
        type=str,
        default=None,
        help="Path to save the podcast episode file without ads.",
    )

    args = parser.parse_args()

    remove_ads(args.file_name, args.out_name, args.notif_name)