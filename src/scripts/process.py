"""Script for Processing scraped data from the DomsDatabasen website.

Examples usages:
    Process single case:
    >>> python src/scripts/process.py 'process.case_id=123'

    Process single case and overwrite existing data:
    >>> python src/scripts/process.py 'case_id=123' 'force=True'

    Process all cases:
    >>> python src/scripts/process.py 'process.force=True'

    Process all cases and overwrite existing data:
    >>> python src/scripts/process.py 'process.force=True' 'process.all=True'
"""

import logging

import hydra
from domsdatabasen.processor import Processor
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


@hydra.main(config_path="../../config", config_name="config")
def main(config: DictConfig) -> None:
    """Process scraped data from the DomsDatabasen website.

    Args:
        config (DictConfig):
            Hydra config object.
    """
    processor = Processor(config=config)
    if config.process.all:
        processor.process_all()
    elif config.process.case_id:
        processor.process(case_id=config.process.case_id)
    else:
        logger.info(
            "Please specify either a 'case_id' or use 'all' to process all cases."
        )

    logger.info("Processing done!")


if __name__ == "__main__":
    main()
