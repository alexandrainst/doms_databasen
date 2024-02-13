"""This scripts finalizes the data by merging all the processed data into a single dataset.

Usage:
    >>> python src/scripts/finalize.py

    Overwrite existing dataset:
    >>> python src/scripts/finalize.py 'finalize.force=True'
"""


import re
from logging import getLogger
from pathlib import Path
from typing import Tuple

import hydra
from omegaconf import DictConfig

from src.doms_databasen.utils import append_jsonl, init_jsonl, read_json

logger = getLogger(__name__)


@hydra.main(config_path="../../config", config_name="config")
def main(config: DictConfig) -> None:
    data_processed_dir = Path(config.paths.data_processed_dir)
    data_final_dir = Path(config.paths.data_final_dir)
    dataset_path = data_final_dir / config.file_names.dataset

    if dataset_path.exists() and not config.finalize.force:
        logger.info(
            f"Dataset already exists at {dataset_path}. Use 'finalize.force=True' to overwrite."
        )
        return

    logger.info("Initializing dataset with path: {dataset_path}")
    init_jsonl(dataset_path)

    processed_case_paths = [
        case_path for case_path in data_processed_dir.iterdir() if case_path.is_dir()
    ]
    logger.info(f"Found {len(processed_case_paths)} cases in {data_processed_dir}")

    # Process cases in ascending order
    processed_case_paths = sorted(processed_case_paths, key=lambda p: int(p.stem))

    for path in processed_case_paths:
        logger.info(f"Processing case {path.stem}...")
        processed_data = read_json(path / config.file_names.processed_data)
        final_data = {}
        final_data["case_id"] = processed_data["case_id"]
        final_data["tabular_data"] = processed_data["tabular_data"]

        text, text_anon = _get_text(processed_data=processed_data, config=config)
        final_data["text"] = text
        final_data["text_anonymized"] = text_anon

        final_data["text_len"] = len(text)
        final_data["text_anon_len"] = len(text_anon)

        append_jsonl(final_data, dataset_path)

    logger.info(f"Dataset saved at {dataset_path}")


def _get_text(processed_data: dict, config: DictConfig) -> Tuple[str, str]:
    """Get `text` and `text_anon` from processed data.

    Args:
        processed_data (dict):
            Processed data for a case.
        config (DictConfig):
            Configuration object.

    Returns:
        text (str):
            Text extracted from the PDF.
        text_anon (str):
            Anonymized text.
    """
    pdf_data = processed_data["pdf_data"]
    if pdf_data["anonymization_method"] == config.anon_method.none:
        # PDF has no anonymization.
        # Make `text_anon` empty.
        # For main `text` use text extracted with Tika.
        # If Tika hasn't been able to read any text,
        # then use text extracted from each page with easyocr.
        if pdf_data["text_tika"]:
            text = pdf_data["text_tika"]
        else:
            text = _get_text_from_pages(pdf_data["pages"])

        text_anon = ""

    elif pdf_data["anonymization_method"] == config.anon_method.underline:
        # PDF uses underline anonymization.
        # Make `text_anon` text extracted from each page.
        # If text is extracted with Tika, then
        # use that for the `text`,
        # else remove anon tags from the anonymized text,
        # and use that for `text`.
        text_anon = _get_text_from_pages(pdf_data["pages"])
        if pdf_data["text_tika"]:
            text = pdf_data["text_tika"]
        else:
            text = re.sub(r"<anonym.*</anonym>", "", text_anon)

    elif pdf_data["anonymization_method"] == config.anon_method.box:
        # PDF uses box anonymization
        # Make `text_anon` text extracted from each page.
        # Remove anon tags from the anonymized text,
        # and use that for `text`.
        text_anon = _get_text_from_pages(pdf_data["pages"])
        text = text = re.sub(r"<anonym.*</anonym>", "", text_anon)

    return text, text_anon


def _get_text_from_pages(pages: dict) -> str:
    """Get text from pages.

    Args:
        pages (dict):
            Pages with text and extraction method.

    Returns:
        pdf_text (str):
            Text from pages.
    """
    pdf_text = "\n\n".join(page["text"] for page in pages.values())
    return pdf_text


if __name__ == "__main__":
    main()
