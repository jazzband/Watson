import re
import arrow
from itertools import combinations
from datetime import datetime, timedelta

import pytest

from watson import cli
from watson.cli import local_tz_info


# Not all ISO-8601 compliant strings are recognized by arrow.get(str)
VALID_DATES_DATA = [
    ('2018', '2018-01-01 00:00:00'),  # years
    ('2018-04', '2018-04-01 00:00:00'),  # calendar dates
    ('2018-04-10', '2018-04-10 00:00:00'),
    ('2018/04/10', '2018-04-10 00:00:00'),
    ('2018.04.10', '2018-04-10 00:00:00'),
    ('2018-4-10', '2018-04-10 00:00:00'),
    ('2018/4/10', '2018-04-10 00:00:00'),
    ('2018.4.10', '2018-04-10 00:00:00'),
    ('20180410', '2018-04-10 00:00:00'),
    ('2018-123', '2018-05-03 00:00:00'),  # ordinal dates
    ('2018-04-10 12:30:43', '2018-04-10 12:30:43'),
    ('2018-04-10T12:30:43', '2018-04-10 12:30:43'),
    ('2018-04-10 12:30:43Z', '2018-04-10 12:30:43'),
    ('2018-04-10 12:30:43.1233', '2018-04-10 12:30:43'),
    ('2018-04-10 12:30:43+03:00', '2018-04-10 12:30:43'),
    ('2018-04-10 12:30:43-07:00', '2018-04-10 12:30:43'),
    ('2018-04-10T12:30:43-07:00', '2018-04-10 12:30:43'),
    ('2018-04-10 12:30', '2018-04-10 12:30:00'),
    ('2018-04-10T12:30', '2018-04-10 12:30:00'),
    ('2018-04-10 12', '2018-04-10 12:00:00'),
    ('2018-04-10T12', '2018-04-10 12:00:00'),
    (
        '14:05:12',
        arrow.now()
        .replace(hour=14, minute=5, second=12)
        .format('YYYY-MM-DD HH:mm:ss')
    ),
    (
        '14:05',
        arrow.now()
        .replace(hour=14, minute=5, second=0)
        .format('YYYY-MM-DD HH:mm:ss')
    ),
    ('2018-W08', '2018-02-19 00:00:00'),  # week dates
    ('2018W08', '2018-02-19 00:00:00'),
    ('2018-W08-2', '2018-02-20 00:00:00'),
    ('2018W082', '2018-02-20 00:00:00'),
]

INVALID_DATES_DATA = [
    (' 2018'),
    ('2018 '),
    ('201804'),
    ('18-04-10'),
    ('180410'),  # truncated representation not allowed
    ('hello 2018'),
    ('yesterday'),
    ('tomorrow'),
    ('14:05:12.000'),  # Times alone are not allowed
    ('140512.000'),
    ('140512'),
    ('14.05'),
    ('2018-04-10T'),
    ('2018-04-10T12:30:43.'),
]

VALID_TIMES_DATA = [
    ('14:12'),
    ('14:12:43'),
    ('2019-04-10T14:12'),
    ('2019-04-10T14:12:43'),
]


class OutputParser:
    FRAME_ID_PATTERN = re.compile(r'id: (?P<frame_id>[0-9a-f]+)')

    @staticmethod
    def get_frame_id(output):
        return OutputParser.FRAME_ID_PATTERN.search(output).group('frame_id')

    @staticmethod
    def get_start_date(watson, output):
        frame_id = OutputParser.get_frame_id(output)
        return watson.frames[frame_id].start.format('YYYY-MM-DD HH:mm:ss')


# watson add

@pytest.mark.parametrize('test_dt,expected', VALID_DATES_DATA)
def test_add_valid_date(runner, watson, test_dt, expected):
    result = runner.invoke(
        cli.add,
        ['-f', test_dt, '-t', test_dt, 'project-name'],
        obj=watson)
    assert result.exit_code == 0
    assert OutputParser.get_start_date(watson, result.output) == expected


@pytest.mark.parametrize('test_dt', INVALID_DATES_DATA)
def test_add_invalid_date(runner, watson, test_dt):
    result = runner.invoke(cli.add,
                           ['-f', test_dt, '-t', test_dt, 'project-name'],
                           obj=watson)
    assert result.exit_code != 0


# watson aggregate

@pytest.mark.parametrize('test_dt,expected', VALID_DATES_DATA)
def test_aggregate_valid_date(runner, watson, test_dt, expected):
    # This is super fast, because no internal 'report' invocations are made
    result = runner.invoke(cli.aggregate,
                           ['-f', test_dt, '-t', test_dt],
                           obj=watson)
    assert result.exit_code == 0


@pytest.mark.parametrize('test_dt', INVALID_DATES_DATA)
def test_aggregate_invalid_date(runner, watson, test_dt):
    # This is super fast, because no internal 'report' invocations are made
    result = runner.invoke(cli.aggregate,
                           ['-f', test_dt, '-t', test_dt],
                           obj=watson)
    assert result.exit_code != 0


# watson log

@pytest.mark.parametrize('cmd', [cli.aggregate, cli.log, cli.report])
def test_incompatible_options(runner, watson, cmd):
    name_interval_options = ['--' + s for s in cli._SHORTCUT_OPTIONS]
    for opt1, opt2 in combinations(name_interval_options, 2):
        result = runner.invoke(cmd, [opt1, opt2], obj=watson)
        assert result.exit_code != 0


@pytest.mark.parametrize('test_dt,expected', VALID_DATES_DATA)
def test_log_valid_date(runner, watson, test_dt, expected):
    result = runner.invoke(cli.log, ['-f', test_dt, '-t', test_dt], obj=watson)
    assert result.exit_code == 0


@pytest.mark.parametrize('test_dt', INVALID_DATES_DATA)
def test_log_invalid_date(runner, watson, test_dt):
    result = runner.invoke(cli.log, ['-f', test_dt, '-t', test_dt], obj=watson)
    assert result.exit_code != 0


# watson report

@pytest.mark.parametrize('test_dt,expected', VALID_DATES_DATA)
def test_report_valid_date(runner, watson, test_dt, expected):
    result = runner.invoke(cli.report,
                           ['-f', test_dt, '-t', test_dt],
                           obj=watson)
    assert result.exit_code == 0


@pytest.mark.parametrize('test_dt', INVALID_DATES_DATA)
def test_report_invalid_date(runner, watson, test_dt):
    result = runner.invoke(cli.report,
                           ['-f', test_dt, '-t', test_dt],
                           obj=watson)
    assert result.exit_code != 0


@pytest.mark.parametrize('cmd', [cli.report, cli.aggregate])
def test_tag_alignment(runner, watson, cmd):
    data = [
        ('foo', 4000, 4020, ['A']),
        ('foo', 5000, 49000, ['B' * 10]),
        ('foo', 50000, 54000, ['C' * 20]),
        ('foo', 55000, 56000, ['D' * 30]),
    ]
    for name, start, end, tags in data:
        watson.frames.add(name, start, end, tags)
    result = runner.invoke(cmd,
                           ['-f', '1970-01-01', '-t', '1970-01-01'],
                           obj=watson)
    lines = result.output.split('\n')
    tag_line_lengths = [len(line) for line in lines if line.startswith('\t[')]
    assert min(tag_line_lengths) == max(tag_line_lengths)


# watson stop

@pytest.mark.parametrize('at_dt', VALID_TIMES_DATA)
def test_stop_valid_time(runner, watson, mocker, at_dt):
    mocker.patch('arrow.arrow.dt_datetime', wraps=datetime)
    start_dt = datetime(2019, 4, 10, 14, 0, 0, tzinfo=local_tz_info())
    arrow.arrow.dt_datetime.now.return_value = start_dt
    result = runner.invoke(cli.start, ['a-project'], obj=watson)
    assert result.exit_code == 0
    # Simulate one hour has elapsed, so that 'at_dt' is older than now()
    # but newer than the start date.
    arrow.arrow.dt_datetime.now.return_value = (start_dt + timedelta(hours=1))
    result = runner.invoke(cli.stop, ['--at', at_dt], obj=watson)
    assert result.exit_code == 0


# watson start

@pytest.mark.parametrize('at_dt', VALID_TIMES_DATA)
def test_start_valid_time(runner, watson, mocker, at_dt):
    # Simulate a start date so that 'at_dt' is older than now().
    mocker.patch('arrow.arrow.dt_datetime', wraps=datetime)
    start_dt = datetime(2019, 4, 10, 14, 0, 0, tzinfo=local_tz_info())
    arrow.arrow.dt_datetime.now.return_value = (start_dt + timedelta(hours=1))
    result = runner.invoke(cli.start, ['a-project', '--at', at_dt], obj=watson)
    assert result.exit_code == 0


# watson start new task in past, with existing task

def test_start_existing_frame_stopped(runner, watson, mocker):
    # Simulate a start date so that 'at_dt' is older than now().
    watson.config.set('options', 'stop_on_start', "true")
    mocker.patch('arrow.arrow.dt_datetime', wraps=datetime)
    start_dt = datetime(2019, 4, 10, 15, 0, 0, tzinfo=local_tz_info())
    arrow.arrow.dt_datetime.now.return_value = start_dt
    runner.invoke(
        cli.start,
        ['a-project', '--at', "14:10"],
        obj=watson,
    )

    result = runner.invoke(
        cli.start,
        ['b-project', '--at', "14:15"],
        obj=watson,
    )
    assert result.exit_code == 0, result.stdout

    frame_id = OutputParser.get_frame_id(result.output)
    assert watson.frames[frame_id].project == "a-project"
    assert watson.current["project"] == "b-project"


# watson restart

@pytest.mark.parametrize('at_dt', VALID_TIMES_DATA)
def test_restart_valid_time(runner, watson, mocker, at_dt):
    # Create a previous entry the same as in `test_stop_valid_time`
    mocker.patch('arrow.arrow.dt_datetime', wraps=datetime)
    start_dt = datetime(2019, 4, 10, 14, 0, 0, tzinfo=local_tz_info())
    arrow.arrow.dt_datetime.now.return_value = start_dt
    result = runner.invoke(cli.start, ['a-project'], obj=watson)
    # Simulate one hour has elapsed, so that 'at_dt' is older than now()
    # but newer than the start date.
    arrow.arrow.dt_datetime.now.return_value = (start_dt + timedelta(hours=1))
    result = runner.invoke(cli.stop, ['--at', at_dt], obj=watson)
    # Test that the last frame can be restarted
    result = runner.invoke(cli.restart, ['--at', at_dt], obj=watson)
    assert result.exit_code == 0
