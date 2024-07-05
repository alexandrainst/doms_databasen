"""Finalize dataset.

This scripts finalizes the data by merging all the processed data into a single dataset.

Usage:
    >>> python src/scripts/finalize.py

    Overwrite existing dataset:
    >>> python src/scripts/finalize.py 'finalize.force=True'
"""


import hydra
from doms_databasen.dataset_builder import DatasetBuilder
from omegaconf import DictConfig


@hydra.main(config_path="../../config", config_name="config")
def main(config: DictConfig) -> None:
    """Finalize dataset.

    Args:
        config (DictConfig):
            Hydra config object.
    """
    dataset_builder = DatasetBuilder(config=config)
    dataset_builder.build_dataset()


if __name__ == "__main__":
    main()
