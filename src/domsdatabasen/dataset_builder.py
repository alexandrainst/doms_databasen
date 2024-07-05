"""DatasetBuilder to build the final dataset."""


import re
from logging import getLogger
from pathlib import Path
from typing import Tuple

from omegaconf import DictConfig

from domsdatabasen._utils import append_jsonl, init_jsonl, read_json

logger = getLogger(__name__)


class DatasetBuilder:
    """DatasetBuilder to build the final dataset.

    Args:
        config (DictConfig):
            Configuration object.

    Attributes:
        config (DictConfig):
            Configuration object.
        data_processed_dir (Path):
            Path to processed data directory.
        data_final_dir (Path):
            Path to final data directory.
        dataset_path (Path):
            Path to the dataset file.
    """

    def __init__(self, config: DictConfig) -> None:
        """Initializes the DatasetBuilder."""
        self.config = config
        self.data_processed_dir = Path(config.paths.data_processed_dir)
        self.data_final_dir = Path(config.paths.data_final_dir)
        self.dataset_path = self.data_final_dir / config.file_names.dataset

    def build_dataset(self) -> None:
        """Build the final dataset."""
        if self.dataset_path.exists() and not self.config.finalize.force:
            logger.info(
                f"Dataset already exists at {self.dataset_path}."
                "Use 'finalize.force=True' to overwrite."
            )
            return

        logger.info("Initializing dataset with path: {dataset_path}")
        init_jsonl(file_name=self.dataset_path)

        processed_case_paths = [
            case_path
            for case_path in self.data_processed_dir.iterdir()
            if case_path.is_dir()
        ]
        logger.info(
            f"Found {len(processed_case_paths)} cases in {self.data_processed_dir}"
        )

        # Process cases in ascending order
        processed_case_paths = sorted(processed_case_paths, key=lambda p: int(p.stem))
        for path in processed_case_paths:
            logger.info(f"Processing case {path.stem}...")
            processed_data = read_json(path / self.config.file_names.processed_data)
            dataset_sample = self.make_dataset_sample(processed_data=processed_data)
            append_jsonl(data=dataset_sample, file_name=self.dataset_path)

        logger.info(f"Dataset saved at {self.dataset_path}")

    def make_dataset_sample(self, processed_data: dict) -> dict:
        """Make a dataset sample from processed data.

        Args:
            processed_data (dict):
                Processed data for a case.

        Returns:
            dataset_sample (dict):
                Dataset sample.
        """
        dataset_sample = {}
        dataset_sample["case_id"] = processed_data["case_id"]
        dataset_sample.update(processed_data["tabular_data"])

        text, text_anon = self._get_text(
            processed_data=processed_data, config=self.config
        )
        dataset_sample["text"] = text
        dataset_sample["text_anonymized"] = text_anon

        dataset_sample["text_len"] = len(text)
        dataset_sample["text_anon_len"] = len(text_anon)
        return dataset_sample

    def _get_text(self, processed_data: dict, config: DictConfig) -> Tuple[str, str]:
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
                text = self._get_text_from_pages(pages=pdf_data["pages"])

            text_anon = ""

        elif pdf_data["anonymization_method"] == config.anon_method.underline:
            # PDF uses underline anonymization.
            # Make `text_anon` text extracted from each page.
            # If text is extracted with Tika, then
            # use that for the `text`,
            # else remove anon tags from the anonymized text,
            # and use that for `text`.
            text_anon = self._get_text_from_pages(pdf_data["pages"])
            if pdf_data["text_tika"]:
                text = pdf_data["text_tika"]
            else:
                text = re.sub(r"<anonym.*</anonym>", "", text_anon)

        elif pdf_data["anonymization_method"] == config.anon_method.box:
            # PDF uses box anonymization
            # Make `text_anon` text extracted from each page.
            # Remove anon tags from the anonymized text,
            # and use that for `text`.
            text_anon = self._get_text_from_pages(pdf_data["pages"])
            text = text = re.sub(r"<anonym.*</anonym>", "", text_anon)

        return text, text_anon

    @staticmethod
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
