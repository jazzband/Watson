"""Provide fixtures for pytest-based unit tests."""

import pytest

from watson import Watson


@pytest.fixture
def config_dir(tmpdir):
    return str(tmpdir.mkdir('config'))


@pytest.fixture
def watson(config_dir):
    return Watson(config_dir=config_dir)
