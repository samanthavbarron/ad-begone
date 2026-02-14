from pathlib import Path
from tqdm import tqdm

from .ad_trimmer import AdTrimmer
from .utils import OPENAI_MODEL, join_files, split_file

from .notif_path import NOTIF_PATH

def remove_ads(
    file_name: str,
    out_name: str | None = None,
    notif_name: str = NOTIF_PATH,
    overwrite: bool = False,
    model: str | None = OPENAI_MODEL,
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
        trimmer = AdTrimmer(split_name, model=model)
        trimmer.remove_ads(notif_name=notif_name)
    print("Joining parts")
    join_files(file_name)
    print("Done")
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
            default=OPENAI_MODEL,
            description="OpenAI model to use for ad classification.",
        )

    parser = pydantic_argparse.ArgumentParser(
        model=RemoveAdsArgs,
        description="Remove ads from a podcast episode.",
    )
    args = parser.parse_typed_args()

    remove_ads(args.file_name, args.out_name, model=args.model)
