"""Session-wide fixtures for tests."""

import shutil

import pytest
from doms_databasen.scraper import Scraper
from hydra import compose, initialize

# Initialise Hydra
initialize(config_path="../../config", version_base=None)


@pytest.fixture(scope="session")
def config():
    """Return a Hydra composed config."""
    return compose(
        config_name="config",
        overrides=["testing=True"],
    )


@pytest.fixture(scope="session")
def scraper(config):
    """Return a Scraper instance."""
    return Scraper(config=config)


def pytest_sessionstart(session):
    """Scrape a single case before running tests."""
    config = compose(
        config_name="config",
        overrides=["testing=True"],
    )
    scraper = Scraper(config=config)
    case_id = str(config.scrape.test_case_id)
    scraper.scrape(case_id=case_id)

    session.__CACHE = scraper.test_dir


def pytest_sessionfinish(session, exitstatus):
    """Delete scraped data after running tests."""
    shutil.rmtree(session.__CACHE)
