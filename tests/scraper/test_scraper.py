"""Test the scraper module."""

from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def test_case_path(config):
    """Return the path to the test case."""
    return Path(config.scrape.paths.test_dir) / config.scrape.test_case_id


def test_case_contains_pdf(config, test_case_path):
    """Test that the test case contains a PDF document."""
    assert (test_case_path / config.file_names.pdf_document).exists()


def test_case_contains_tabular_data(config, test_case_path):
    """Test that the test case contains tabular data."""
    assert (test_case_path / config.file_names.tabular_data).exists()


if __name__ == "__main__":
    pytest.main([f"{__file__}::test_case_contains_pdf", "-s"])
