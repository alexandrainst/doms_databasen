"""Processor for scraped data from domsdatabasen.dk."""

import os
import time
from logging import getLogger
from pathlib import Path
from typing import Dict, List, Union

import torch
from omegaconf import DictConfig

from ._constants import N_FILES_PROCESSED_CASE_DIR, N_FILES_RAW_CASE_DIR
from ._text_extraction import PDFTextReader
from ._utils import load_jsonl, read_json, save_dict_to_json

logger = getLogger(__name__)


class Processor(PDFTextReader):
    """Processor for scraped data from the DomsDatabasen website.

    Args:
        config (DictConfig):
            Config file

    Attributes:
        config (DictConfig):
            Config file
        data_raw_dir (Path):
            Path to raw data directory
        data_processed_dir (Path):
            Path to processed data directory
        force (bool):
            If True, existing data will be overwritten.
    """

    def __init__(self, config: DictConfig) -> None:
        """Initializes the Processor."""
        super().__init__(config=config)
        self.config = config

        self.data_raw_dir = (
            Path(self.config.paths.data_raw_dir)
            if not self.config.testing
            else Path(self.config.process.paths.test_data_raw_dir)
        )

        self.data_processed_dir = (
            Path(self.config.paths.data_processed_dir)
            if not self.config.testing
            else Path(self.config.process.paths.test_data_processed_dir)
        )

        self.force = self.config.process.force
        self.blacklist = self._read_blacklist() if config.process.blacklist_flag else []

    def process(self, case_id: str) -> Dict[str, Union[str, Dict[str, str]]]:
        """Processes a single case.

        This function takes the raw tabular data and
        adds the text from the pdf to it + the ID of the case.

        Args:
            case_id (str):
                Case ID

        Returns:
            processed_data (dict):
                Processed data (only returned for testing purposes)
        """
        processed_data: Dict[str, Union[str, Dict[str, str]]] = {}

        case_id = str(case_id)
        if case_id in self.blacklist:
            logger.info(f"{case_id} is blacklisted.")
            return {}
        start = time.time()
        case_id = str(case_id)

        case_dir_raw = self.data_raw_dir / case_id
        case_dir_processed = self.data_processed_dir / case_id

        # Check if raw data for case ID exists.
        if not self._raw_data_exists(case_dir=case_dir_raw):
            logger.info(f"Case {case_id} does not exist in raw data directory.")
            return {}

        # If case has already been processed, skip, unless force=True.
        if self._already_processed(case_dir=case_dir_processed) and not self.force:
            logger.info(
                f"Case {case_id} has already been processed. Use --force to overwrite."
            )
            processed_data = read_json(
                file_path=case_dir_processed / self.config.file_names.processed_data
            )
            return processed_data

        # Process data for the case.
        logger.info(f"Processing case {case_id}...")

        case_dir_processed.mkdir(parents=True, exist_ok=True)

        tabular_data: Dict[str, str] = read_json(
            case_dir_raw / self.config.file_names.tabular_data
        )

        processed_data["case_id"] = case_id
        processed_data["tabular_data"] = tabular_data

        pdf_path = case_dir_raw / self.config.file_names.pdf_document
        pdf_data = self.extract_text(
            pdf_path=pdf_path,
        )
        processed_data["pdf_data"] = pdf_data
        processed_data["process_info"] = {
            "process_time": str(time.time() - start),
            "hardware_used": "gpu" if torch.cuda.is_available() else "cpu",
        }

        if not self.config.testing:
            save_dict_to_json(
                processed_data,
                case_dir_processed / self.config.file_names.processed_data,
            )

        logger.info(f"Done with case: {case_id}")

        # Return data for testing purposes.
        return processed_data

    def process_all(self) -> None:
        """Processes all cases in data/raw."""
        logger.info("Processing all cases...")
        case_ids = sorted(
            [
                case_path.name
                for case_path in self.data_raw_dir.iterdir()
                if case_path.is_dir()  # Exclude .gitkeep
            ],
            key=lambda case_id: int(case_id),
        )

        start_case_id = self.config.process.start_case_id
        if start_case_id:
            case_ids = case_ids[case_ids.index(start_case_id) :]

        for case_id in case_ids:
            self.process(case_id)

    def _already_processed(self, case_dir) -> bool:
        """Checks if a case has already been processed.

        If a case has already been processed, the case directory will
        exist and will contain one file with the tabular data.

        Args:
            case_dir (Path):
                Path to case directory

        Returns:
            bool:
                True if case has already been processed. False otherwise.
        """
        return (
            case_dir.exists()
            and len(os.listdir(case_dir)) == N_FILES_PROCESSED_CASE_DIR
        )

    def _raw_data_exists(self, case_dir) -> bool:
        """Checks if raw data for a case exists.

        If a case has been scraped successfully, then the case directory exists
        and contains two files: the PDF document and the tabular data.

        Same code as the method `_already_scraped` from class `Scraper`
        (src/domsdatabasen/scraper.py).

        Args:
            case_dir (Path):
                Path to case directory

        Returns:
            bool:
                True if case has already been scraped. False otherwise.
        """
        return case_dir.exists() and len(os.listdir(case_dir)) == N_FILES_RAW_CASE_DIR

    def _read_blacklist(self) -> List[str]:
        """Reads the blacklised cases.

        Returns:
            list of str:
                List of blacklisted cases.
        """
        data = load_jsonl(self.config.process.paths.blacklist)
        blacklist = [str(item["case_id"]) for item in data]
        return blacklist
