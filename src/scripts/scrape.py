"""Script for scraping the DomsDatabasen website.

Examples usages:
    Scrape single case:
    >>> python src/scripts/scrape.py --case_id=123

    Scrape single case and overwrite existing data:
    >>> python src/scripts/scrape.py --case_id=123 --force

    Scrape all cases:
    >>> python src/scripts/scrape.py

    Scrape all cases and overwrite existing data:
    >>> python src/scripts/scrape.py --force
"""

import logging

import click

from src.doms_databasen.utils import read_config
from src.doms_databasen.scraper import DomsDatabasenScraper

logger = logging.getLogger(__name__)


@click.command()
@click.option("--force", is_flag=True, default=False, help="Force scraping")
@click.option("--case_id", type=str, default="", help="Specify a case ID to scrape")
@click.option("--scrape_all", is_flag=True, default=False, help="Scrape all cases")
def main(force: bool, case_id: str, scrape_all: bool):
    cfg = read_config(config_path="../../config", config_name="config")
    if (not case_id and not scrape_all) or (case_id and scrape_all):
        logger.info(cfg.messages.give_correct_inputs)
        exit()

    scraper = DomsDatabasenScraper(cfg=cfg)
    if scrape_all:
        logger.info("Scraping all cases")
        scraper.scrape_all(force=force)
    else:
        logger.info(f"Scraping case {case_id}")
        scraper.scrape_case(case_id, force=force)

    logger.info("Done!")


if __name__ == "__main__":
    main()
