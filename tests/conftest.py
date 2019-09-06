"""Provide fixtures for pytest-based unit tests."""

from click.testing import CliRunner
import os
import py
import pytest

from watson import Watson


TEST_FIXTURE_DIR = py.path.local(
    os.path.dirname(
        os.path.realpath(__file__)
        )
    ) / 'resources'


@pytest.fixture
def config_dir(tmpdir):
    return str(tmpdir.mkdir('config'))


@pytest.fixture
def watson(config_dir):
    return Watson(config_dir=config_dir)


@pytest.fixture
def runner():
    return CliRunner()
