"""Unit tests for the 'utils' module."""

import datetime
import functools
import os
import uuid

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import pytest
from dateutil.tz import tzutc

from watson.config import ConfigParser
from watson.utils import (get_start_time_for_period, format_short_id,
                          format_tags,  make_json_writer, safe_save, style)
from . import mock_datetime, mock_read


_dt = functools.partial(datetime.datetime, tzinfo=tzutc())


@pytest.mark.parametrize('now, mode, start_time', [
    (_dt(2016, 6, 2), 'year', _dt(2016, 1, 1)),
    (_dt(2016, 6, 2), 'month', _dt(2016, 6, 1)),
    (_dt(2016, 6, 2), 'week', _dt(2016, 5, 30)),
    (_dt(2016, 6, 2), 'day', _dt(2016, 6, 2)),

    (_dt(2012, 2, 24), 'year', _dt(2012, 1, 1)),
    (_dt(2012, 2, 24), 'month', _dt(2012, 2, 1)),
    (_dt(2012, 2, 24), 'week', _dt(2012, 2, 20)),
    (_dt(2012, 2, 24), 'day', _dt(2012, 2, 24)),
])
def test_get_start_time_for_period(now, mode, start_time):
    with mock_datetime(now, datetime):
        assert get_start_time_for_period(mode).datetime == start_time


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


@pytest.mark.parametrize('element, expected', [
    ('project', '\x1b[35m{}\x1b[0m'),
    ('tag', '\x1b[34m{}\x1b[0m'),
    ('time', '\x1b[32m{}\x1b[0m'),
    ('error', '\x1b[31m{}\x1b[0m'),
    ('date', '\x1b[36m{}\x1b[0m'),
    ('id', '\x1b[37m{}\x1b[0m'),
])
def test_style_no_context(element, expected):
    assert style(element, 'foo') == expected.format('foo')


@pytest.mark.parametrize('element, expected', [
    ('project', '\x1b[32m{}\x1b[0m'),
    ('tag', '\x1b[33m{}\x1b[0m'),
])
def test_style_with_context(element, expected, mock):
    content = u"""
[style:project]
fg = green
[style:tag]
fg = yellow
    """
    mock.patch.object(ConfigParser, 'read', mock_read(content))
    config = ConfigParser()
    config.read('dummy')
    mock_get_ctx = mock.Mock(
        return_value=mock.Mock(obj=mock.Mock(config=config)))
    mock.patch('click.get_current_context', mock_get_ctx)
    assert style(element, 'foo') == expected.format('foo')


def test_format_short_id():
    id_ = uuid.uuid4().hex
    assert format_short_id(id_) == '\x1b[37m{}\x1b[0m'.format(id_[:7])


def test_format_tags():
    tags = ['foo', 'bar']
    assert format_tags([]) == ''
    assert format_tags(tags) == '[\x1b[34mfoo\x1b[0m, \x1b[34mbar\x1b[0m]'
