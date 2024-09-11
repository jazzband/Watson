"""Unit tests for the 'utils' module."""

import arrow
import collections as co
import csv
import functools
import json
import os
import datetime
import operator
from io import StringIO
from unittest.mock import patch
import pytest
from click.exceptions import Abort
from dateutil.tz import tzutc

from watson.utils import (
    apply_weekday_offset,
    build_csv,
    confirm_project,
    confirm_tags,
    flatten_report_for_csv,
    frames_to_csv,
    frames_to_json,
    get_start_time_for_period,
    make_json_writer,
    safe_save,
    sorted_groupby,
    parse_tags,
    json_arrow_encoder,
)
from . import mock_datetime


_dt = functools.partial(datetime.datetime, tzinfo=tzutc())


@pytest.mark.parametrize('now, mode, start_time', [
    (_dt(2016, 6, 2), 'year', _dt(2016, 1, 1)),
    (_dt(2016, 6, 2), 'month', _dt(2016, 6, 1)),
    (_dt(2016, 6, 2), 'week', _dt(2016, 5, 30)),
    (_dt(2016, 6, 2), 'day', _dt(2016, 6, 2)),
    (_dt(2016, 6, 2), 'all', _dt(1970, 1, 1)),
    (_dt(2016, 6, 2), 'luna', _dt(2016, 5, 21, 21, 16)),

    (_dt(2012, 2, 24), 'year', _dt(2012, 1, 1)),
    (_dt(2012, 2, 24), 'month', _dt(2012, 2, 1)),
    (_dt(2012, 2, 24), 'week', _dt(2012, 2, 20)),
    (_dt(2012, 2, 24), 'day', _dt(2012, 2, 24)),
    (_dt(2012, 2, 24), 'all', _dt(1970, 1, 1)),
    (_dt(2012, 2, 24), 'luna', _dt(2012, 2, 7, 21, 56)),
])
def test_get_start_time_for_period(now, mode, start_time):
    with mock_datetime(now, datetime):
        assert get_start_time_for_period(mode).datetime == start_time


@pytest.mark.parametrize("monday_start, week_start, new_start", [
    ("2018 12 3", "monday", "2018 12 3"),
    ("2018 12 3", "tuesday", "2018 12 4"),
    ("2018 12 3", "wednesday", "2018 12 5"),
    ("2018 12 3", "thursday", "2018 12 6"),
    ("2018 12 3", "friday", "2018 11 30"),
    ("2018 12 3", "saturday", "2018 12 1"),
    ("2018 12 3", "sunday", "2018 12 2"),
    ("2018 12 3", "typo", "2018 12 3"),
])
def test_apply_weekday_offset(monday_start, week_start, new_start):
    with mock_datetime(_dt(2018, 12, 6), datetime):
        original_start = arrow.get(monday_start, "YYYY MM D")
        result = arrow.get(new_start, "YYYY MM D")
        assert apply_weekday_offset(original_start, week_start) == result


def test_make_json_writer():
    fp = StringIO()
    writer = make_json_writer(lambda: {'foo': 42})
    writer(fp)
    assert fp.getvalue() == '{\n "foo": 42\n}'


def test_make_json_writer_with_args():
    fp = StringIO()
    writer = make_json_writer(lambda x: {'foo': x}, 23)
    writer(fp)
    assert fp.getvalue() == '{\n "foo": 23\n}'


def test_make_json_writer_with_kwargs():
    fp = StringIO()
    writer = make_json_writer(lambda foo=None: {'foo': foo}, foo='bar')
    writer(fp)
    assert fp.getvalue() == '{\n "foo": "bar"\n}'


def test_make_json_writer_with_unicode():
    fp = StringIO()
    writer = make_json_writer(lambda: {'ùñï©ôð€': 'εvεrywhεrε'})
    writer(fp)
    expected = '{\n "ùñï©ôð€": "εvεrywhεrε"\n}'
    assert fp.getvalue() == expected


def test_safe_save(config_dir):
    save_file = os.path.join(config_dir, 'test')
    backup_file = os.path.join(config_dir, 'test' + '.bak')

    assert not os.path.exists(save_file)
    safe_save(save_file, lambda f: f.write("Success"))
    assert os.path.exists(save_file)
    assert not os.path.exists(backup_file)

    with open(save_file) as fp:
        assert fp.read() == "Success"

    safe_save(save_file, "Again")
    assert os.path.exists(backup_file)

    with open(save_file) as fp:
        assert fp.read() == "Again"

    with open(backup_file) as fp:
        assert fp.read() == "Success"

    assert os.path.getmtime(save_file) >= os.path.getmtime(backup_file)


def test_safe_save_tmpfile_on_other_filesystem(config_dir, mocker):
    save_file = os.path.join(config_dir, 'test')
    backup_file = os.path.join(config_dir, 'test' + '.bak')

    assert not os.path.exists(save_file)
    safe_save(save_file, lambda f: f.write("Success"))
    assert os.path.exists(save_file)
    assert not os.path.exists(backup_file)

    with open(save_file) as fp:
        assert fp.read() == "Success"

    # simulate tmpfile being on another file-system
    # OSError is caught and handled by shutil.move() used by save_safe()
    mocker.patch('os.rename', side_effect=OSError)
    safe_save(save_file, "Again")
    assert os.path.exists(backup_file)

    with open(save_file) as fp:
        assert fp.read() == "Again"


def test_safe_save_with_exception(config_dir):
    save_file = os.path.join(config_dir, 'test')
    backup_file = os.path.join(config_dir, 'test' + '.bak')

    def failing_writer(f):
        raise RuntimeError("Save failed.")

    assert not os.path.exists(save_file)

    with pytest.raises(RuntimeError):
        safe_save(save_file, failing_writer)

    assert not os.path.exists(save_file)
    assert not os.path.exists(backup_file)

    safe_save(save_file, lambda f: f.write("Success"))
    assert os.path.exists(save_file)
    assert not os.path.exists(backup_file)

    with pytest.raises(RuntimeError):
        safe_save(save_file, failing_writer)

    with open(save_file) as fp:
        assert fp.read() == "Success"

    assert not os.path.exists(backup_file)


@pytest.mark.parametrize('args, parsed_tags', [
    (['+ham', '+n', '+eggs'], ['ham', 'n', 'eggs']),
    (['+ham', 'n', '+eggs'], ['ham n', 'eggs']),
    (['ham', 'n', '+eggs'], ['eggs']),
    (['ham', '+n', 'eggs'], ['n eggs']),
    (['+ham', 'n', 'eggs'], ['ham n eggs']),
])
def test_parse_tags(args, parsed_tags):
    tags = parse_tags(args)
    assert tags == parsed_tags


def test_confirm_project_existing_project_returns_true():
    project = 'foo'
    watson_projects = ['foo', 'bar']
    assert confirm_project(project, watson_projects)


@patch('click.confirm', return_value=True)
def test_confirm_project_accept_returns_true(confirm):
    project = 'baz'
    watson_projects = ['foo', 'bar']
    assert confirm_project(project, watson_projects)


@patch('watson.utils.click.confirm', side_effect=Abort)
def test_confirm_project_reject_raises_abort(confirm):
    project = 'baz'
    watson_projects = ['foo', 'bar']
    with pytest.raises(Abort):
        confirm_project(project, watson_projects)


def test_confirm_tags_existing_tag_returns_true():
    tags = ['a']
    watson_tags = ['a', 'b']
    assert confirm_tags(tags, watson_tags)


@patch('click.confirm', return_value=True)
def test_confirm_tags_accept_returns_true(confirm):
    tags = ['c']
    watson_tags = ['a', 'b']
    assert confirm_tags(tags, watson_tags)


@patch('click.confirm', side_effect=Abort)
def test_confirm_tags_reject_raises_abort(confirm):
    tags = ['c']
    watson_tags = ['a', 'b']
    with pytest.raises(Abort):
        confirm_project(tags[0], watson_tags)


# build_csv

def test_build_csv_empty_data():
    assert build_csv([]) == ''


def test_build_csv_one_col():
    lt = os.linesep
    data = [{'col': 'value'}, {'col': 'another value'}]
    result = lt.join(['col', 'value', 'another value']) + lt
    assert build_csv(data) == result


def test_build_csv_multiple_cols():
    lt = os.linesep
    dm = csv.get_dialect('excel').delimiter
    data = [
        co.OrderedDict([('col1', 'value'),
                        ('col2', 'another value'),
                        ('col3', 'more')]),
        co.OrderedDict([('col1', 'one value'),
                        ('col2', 'two value'),
                        ('col3', 'three')])
    ]
    result = lt.join([
        dm.join(['col1', 'col2', 'col3']),
        dm.join(['value', 'another value', 'more']),
        dm.join(['one value', 'two value', 'three'])
        ]) + lt
    assert build_csv(data) == result


# sorted_groupby

def test_sorted_groupby(watson):
    end = arrow.utcnow()
    watson.add('foo', end.shift(hours=-25), end.shift(hours=-24), ['A'])
    watson.add('bar', end.shift(hours=-1), end, ['A'])

    result = list(sorted_groupby(
        watson.frames,
        operator.attrgetter('day'),
        reverse=False))
    assert result[0][0] < result[1][0]


def test_sorted_groupby_reverse(watson):
    end = arrow.utcnow()
    watson.add('foo', end.shift(hours=-25), end.shift(hours=-24), ['A'])
    watson.add('bar', end.shift(hours=-1), end, ['A'])

    result = list(sorted_groupby(
        watson.frames,
        operator.attrgetter('day'),
        reverse=True))
    assert result[0][0] > result[1][0]


# frames_to_csv

def test_frames_to_csv_empty_data(watson):
    assert frames_to_csv(watson.frames) == ''


def test_frames_to_csv(watson):
    watson.start('foo', tags=['A', 'B'])
    watson.stop()

    result = frames_to_csv(watson.frames)

    read_csv = list(csv.reader(StringIO(result)))
    header = ['id', 'start', 'stop', 'project', 'tags']
    assert len(read_csv) == 2
    assert read_csv[0] == header
    assert read_csv[1][3] == 'foo'
    assert read_csv[1][4] == 'A, B'


# frames_to_json

def test_frames_to_json_empty_data(watson):
    assert frames_to_json(watson.frames) == '[]'


def test_frames_to_json(watson):
    watson.start('foo', tags=['A', 'B'])
    watson.stop()

    result = json.loads(frames_to_json(watson.frames))

    keys = {'id', 'start', 'stop', 'project', 'tags'}
    assert len(result) == 1
    assert set(result[0].keys()) == keys
    assert result[0]['project'] == 'foo'
    assert result[0]['tags'] == ['A', 'B']


# flatten_report_for_csv

def test_flatten_report_for_csv(watson):
    now = arrow.utcnow().ceil('hour')
    watson.add('foo', now.shift(hours=-4), now, ['A', 'B'])
    watson.add('foo', now.shift(hours=-5), now.shift(hours=-4), ['A'])
    watson.add('foo', now.shift(hours=-7), now.shift(hours=-5), ['B'])

    start = now.shift(days=-1)
    stop = now
    result = flatten_report_for_csv(watson.report(start, stop))

    assert len(result) == 3

    assert result[0]['from'] == start.format('YYYY-MM-DD 00:00:00')
    assert result[0]['to'] == stop.format('YYYY-MM-DD 23:59:59')
    assert result[0]['project'] == 'foo'
    assert result[0]['tag'] == ''
    assert result[0]['time'] == (4 + 1 + 2) * 3600

    assert result[1]['from'] == start.format('YYYY-MM-DD 00:00:00')
    assert result[1]['to'] == stop.format('YYYY-MM-DD 23:59:59')
    assert result[1]['project'] == 'foo'
    assert result[1]['tag'] == 'A'
    assert result[1]['time'] == (4 + 1) * 3600

    assert result[2]['from'] == start.format('YYYY-MM-DD 00:00:00')
    assert result[2]['to'] == stop.format('YYYY-MM-DD 23:59:59')
    assert result[2]['project'] == 'foo'
    assert result[2]['tag'] == 'B'
    assert result[2]['time'] == (4 + 2) * 3600


def test_json_arrow_encoder():
    with pytest.raises(TypeError):
        json_arrow_encoder(0)

    with pytest.raises(TypeError):
        json_arrow_encoder('foo')

    with pytest.raises(TypeError):
        json_arrow_encoder(None)

    now = arrow.utcnow()
    assert json_arrow_encoder(now) == now.for_json()
