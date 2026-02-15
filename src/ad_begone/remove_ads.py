import logging
from pathlib import Path
from tqdm import tqdm

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

    split_names = split_file(file_name)
    for split_name in tqdm(split_names, desc="Splitting parts"):
        trimmer = AdTrimmer(split_name, model=model)
        trimmer.remove_ads(notif_name=notif_name)
    logger.info("Joining parts for %s", file_name)
    join_files(file_name)
    logger.info("Done processing %s", file_name)
    path_file_hit.write_text("")

if __name__ == "__main__":
    from typing import Optional

    from pydantic import BaseModel, Field
    import pydantic2_argparse

    class RemoveAdsArgs(BaseModel):
        file_name: str = Field(
            description="Path to the podcast episode file.",
        )
        out_name: Optional[str] = Field(
            default=None,
            description="Path to save the podcast episode file without ads.",
        )
        model: Optional[str] = Field(
            default=None,
            description="OpenAI model to use for ad classification.",
        )

    parser = pydantic2_argparse.ArgumentParser(
        model=RemoveAdsArgs,
        description="Remove ads from a podcast episode.",
    )
    args = parser.parse_typed_args()

    remove_ads(args.file_name, args.out_name, model=args.model)
