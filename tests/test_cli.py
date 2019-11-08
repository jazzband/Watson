import pytest

from click import testing
from watson.cli import cli


@pytest.fixture
def runner():
    return testing.CliRunner()


def test_cli(runner):

    result = runner.invoke(cli)
    assert result.exit_code == 0
