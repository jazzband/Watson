from watson import cli
from click.testing import CliRunner
import json
import os
import arrow
import pytest

@pytest.fixture
def setup(tmpdir):
    os.environ["WATSON_DIR"] = tmpdir.strpath

# test for watson add <project> --from "hh:mm" --to "hh:mm"
def test_time_only(setup):
    
    runner = CliRunner()

    test_data = [("13:00", "15:00"),
                 ("3:00", "17:00"),
                 ("1:00", "3:41")]

    project = "test_time_only"
    data_index = 0

    for data in test_data:
        from_time = data[0]
        to_time = data[1]

        result = runner.invoke(cli.cli, ["add", project, '--from' , from_time, '--to', to_time])

        result = runner.invoke(cli.cli, ["log", "-j"])
        output = json.loads(result.output)[data_index]

        assert output["project"] == project
        today = arrow.now().floor("day").format("YYYY-MM-DD")
        assert today in output["start"]
        assert from_time in output["start"]
        assert today in output["stop"]
        assert to_time in output["stop"]

        data_index += 1

# test for watson add <project> --from "yyyy-mm-dd hh:mm" --to "hh:mm"
def test_from_date_time(setup):
    runner = CliRunner()

    test_data = [("2016-03-24", "07:32", "08:54"),
                 ("2017-04-28", "14:00", "17:31")]

    project = "test_date_time"

    for data in test_data:
        date = data[0]
        from_time = data[1]
        to_time = data[2]

        result = runner.invoke(cli.cli, ["add", project, '--from' , "{} {}".format(date, from_time), '--to', to_time])

        # as watson log -a crashes, I use -f <date>
        result = runner.invoke(cli.cli, ["log", "-f", date, "-j"])
        runner.invoke(cli.cli, ["log"])
        output = json.loads(result.output)[0]

        assert output["project"] == project
        assert date in output["start"]
        assert from_time in output["start"]
        assert date in output["stop"]
        assert to_time in output["stop"]

def test_format_not_supported(setup):
    runner = CliRunner()

    result = runner.invoke(cli.cli, ["add", "test", "--from", "crash 13:30", "--to", "13:37"])
    assert "Format not supported" in result.output
