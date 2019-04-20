# -*- coding: utf-8 -*-
"""Unit tests for the 'utils' module."""

import arrow
import functools
import os
import datetime

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import pytest
from unittest.mock import patch
from click.exceptions import Abort
from dateutil.tz import tzutc

import watson
from watson.utils import (apply_weekday_offset, get_start_time_for_period,
                          make_json_writer, safe_save, parse_tags, PY2,
                          confirm_project, confirm_tags)
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
    writer = make_json_writer(lambda: {u'ùñï©ôð€': u'εvεrywhεrε'})
    writer(fp)
    expected = u'{\n "ùñï©ôð€": "εvεrywhεrε"\n}'
    if PY2:
        expected = expected.encode('utf-8')
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


def test_safe_save_tmpfile_on_other_filesystem(config_dir, mock):
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
    mock.patch('os.rename', side_effect=OSError)
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
    projects = ['foo', 'bar']
    assert confirm_project(project, projects)


@patch('click.confirm', return_value=True)
def test_confirm_project_accept_returns_true(confirm):
    project = 'baz'
    projects = ['foo', 'bar']
    assert confirm_project(project, projects)


@patch('watson.utils.click.confirm', side_effect=Abort)
def test_confirm_project_reject_raises_abort(confirm):
    project = 'baz'
    projects = ['foo', 'bar']
    with pytest.raises(Abort) as e:
            confirm_project(project, projects)


def test_confirm_tags_existing_tag_returns_true():
    tags = ['a']
    watson_tags = ['a', 'b']
    assert confirm_tags(tags, watson_tags)


@patch('watson.utils.click.confirm', return_value=True)
def test_confirm_tags_accept_returns_true(confirm):
    tags = ['c']
    watson_tags = ['a', 'b']
    assert confirm_tags(tags, watson_tags)


@patch('watson.utils.click.confirm', side_effect=Abort)
def test_confirm_tags_reject_raises_abort(confirm):
    tags = ['c']
    watson_tags = ['a', 'b']
    with pytest.raises(Abort) as e:
            confirm_project(tags, watson_tags)