"""Upload the Domsdatabasen dataset to Huggingface

Usage:
    >>> python src/scripts/push_to_hub.py
"""


import logging

import hydra
from datasets import load_dataset
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


@hydra.main(config_path="../../config", config_name="config")
def main(config: DictConfig) -> None:
    dataset = load_dataset(config.paths.data_final_dir)
    dataset.push_to_hub(config.hf_hub, private=True)


if __name__ == "__main__":
    main()
