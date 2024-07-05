"""Code for testing the Processor class."""


import pytest
from domsdatabasen.processor import Processor


@pytest.fixture(scope="module")
def processor(config):
    """Return a Processor instance."""
    return Processor(config=config)


@pytest.fixture(scope="module")
def processed_data(config, processor):
    """Return processed data for testing purposes."""
    return processor.process(case_id=config.process.test_case_id)


@pytest.mark.parametrize(
    "key",
    ["case_id", "tabular_data", "pdf_data", "process_info"],
)
def test_tabular_data(processed_data, key):
    """Test that the processed data contains the expected keys."""
    assert processed_data[key]


if __name__ == "__main__":
    pytest.main([__file__ + "::test_tabular_data", "-s"])
