from pathlib import Path

from ad_begone.ad_trimmer import AdTrimmer
from ad_begone.utils import join_files, split_file


def remove_ads(
    file_name: str,
    out_name: str | None = None,
    notif_name: str = "src/ad_begone/notif.mp3",
):
    if out_name is None:
        out_name = file_name
    
    path = Path(file_name)
    path_file_hit = path.parent / f".hit.{path.name}.txt"

    if path_file_hit.exists():
        print("Already hit")
        return
    
    split_names = split_file(file_name)
    for split_name in split_names:
        trimmer = AdTrimmer(split_name)
        trimmer.remove_ads(notif_name=notif_name)
    join_files(file_name)

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