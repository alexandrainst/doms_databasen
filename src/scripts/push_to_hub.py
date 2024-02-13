"""Upload the Domsdatabasen dataset to Huggingface

Usage:
    >>> python src/scripts/push_to_hub.py
"""


import logging
from pathlib import Path

import hydra
from datasets import load_dataset
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


@hydra.main(config_path="../../config", config_name="config")
def main(config: DictConfig) -> None:
    dataset = load_dataset(config.paths.data_final_dir)

    # Ensure that there is one sample in the
    # dataset for each processed case
    assert dataset.num_rows["train"] == _count_folders_in_dir(
        Path(config.paths.data_processed_dir)
    )

    dataset.push_to_hub(config.hf_hub, private=True)


def _count_folders_in_dir(dir: Path) -> int:
    return len([f for f in dir.iterdir() if f.is_dir()])


if __name__ == "__main__":
    main()
