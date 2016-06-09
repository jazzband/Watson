import sys
import json
import os
import datetime

try:
    from unittest import mock
except ImportError:
    import mock

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import py
import pytest
import requests
import arrow

from dateutil.tz.tz import tzutc

from click import get_app_dir
from watson import Watson, WatsonError
from watson.frames import Frame, Frames
from watson.watson import ConfigurationError, ConfigParser
from watson.utils import get_start_time_for_period, make_json_writer, safe_save


TEST_FIXTURE_DIR = py.path.local(
    os.path.dirname(
        os.path.realpath(__file__)
        )
    ) / 'resources'

PY2 = sys.version_info[0] == 2

if not PY2:
    builtins = 'builtins'
else:
    builtins = '__builtin__'


def mock_datetime(dt, dt_module):

    class DateTimeMeta(type):

        @classmethod
        def __instancecheck__(mcs, obj):
            return isinstance(obj, datetime.datetime)

    class BaseMockedDateTime(datetime.datetime):

        @classmethod
        def now(cls, tz=None):
            return dt.replace(tzinfo=tz)

        @classmethod
        def utcnow(cls):
            return dt

        @classmethod
        def today(cls):
            return dt

    MockedDateTime = DateTimeMeta('datetime', (BaseMockedDateTime,), {})

    return mock.patch.object(dt_module, 'datetime', MockedDateTime)


@pytest.fixture
def config_dir(tmpdir):
    return str(tmpdir.mkdir('config'))


def mock_read(content):
    return lambda self, name: self._read(StringIO(content), name)


@pytest.fixture
def watson(config_dir):
    return Watson(config_dir=config_dir)


# current

def test_current(watson):
    content = json.dumps({'project': 'foo', 'start': 0, 'tags': ['A', 'B']})

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.current['project'] == 'foo'
        assert watson.current['start'] == arrow.get(0)
        assert watson.current['tags'] == ['A', 'B']


def test_current_with_empty_file(watson):
    with mock.patch('%s.open' % builtins, mock.mock_open(read_data="")):
        with mock.patch('os.path.getsize', return_value=0):
            assert watson.current == {}


def test_current_with_nonexistent_file(watson):
    with mock.patch('%s.open' % builtins, side_effect=IOError):
        assert watson.current == {}


def test_current_watson_non_valid_json(watson):
    content = "{'foo': bar}"

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        with mock.patch('os.path.getsize', return_value=len(content)):
            with pytest.raises(WatsonError):
                watson.current


def test_current_with_given_state(config_dir):
    content = json.dumps({'project': 'foo', 'start': 0})
    watson = Watson(current={'project': 'bar', 'start': 0},
                    config_dir=config_dir)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.current['project'] == 'bar'


def test_current_with_empty_given_state(config_dir):
    content = json.dumps({'project': 'foo', 'start': 0})
    watson = Watson(current=[], config_dir=config_dir)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.current == {}


# last_sync

def test_last_sync(watson):
    now = arrow.get(123)
    content = json.dumps(now.timestamp)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.last_sync == now


def test_last_sync_with_empty_file(watson):
    with mock.patch('%s.open' % builtins, mock.mock_open(read_data="")):
        with mock.patch('os.path.getsize', return_value=0):
            assert watson.last_sync == arrow.get(0)


def test_last_sync_with_nonexistent_file(watson):
    with mock.patch('%s.open' % builtins, side_effect=IOError):
        assert watson.last_sync == arrow.get(0)


def test_last_sync_watson_non_valid_json(watson):
    content = "{'foo': bar}"

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        with mock.patch('os.path.getsize', return_value=len(content)):
            with pytest.raises(WatsonError):
                watson.last_sync


def test_last_sync_with_given_state(config_dir):
    content = json.dumps(123)
    now = arrow.now()
    watson = Watson(last_sync=now, config_dir=config_dir)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.last_sync == now


def test_last_sync_with_empty_given_state(config_dir):
    content = json.dumps(123)
    watson = Watson(last_sync=None, config_dir=config_dir)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.last_sync == arrow.get(0)


# frames

def test_frames(watson):
    content = json.dumps([['abcdefg', 'foo', 0, 10, ['A', 'B', 'C']]])

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 1
        frame = watson.frames['abcdefg']
        assert frame.id == 'abcdefg'
        assert frame.project == 'foo'
        assert frame.start == arrow.get(0)
        assert frame.stop == arrow.get(10)
        assert frame.tags == ['A', 'B', 'C']


def test_frames_from_sequence_of_tuples(watson):
    test_frames = (
        ('0', 'project0',  0, 10),
        ('1', 'project1', 10, 20, ['A', 'B', 'C'])
    )
    watson.frames = test_frames

    assert len(watson.frames) == 2
    assert isinstance(watson.frames, Frames)

    frame = watson.frames.get_by_index(0)
    assert isinstance(frame, Frame)
    assert frame.id == '0'
    assert frame.project == 'project0'
    assert frame.start == arrow.get(0)
    assert frame.stop == arrow.get(10)

    frame = watson.frames.get_by_index(1)
    assert isinstance(frame, Frame)
    assert frame.id == '1'
    assert frame.project == 'project1'
    assert frame.start == arrow.get(10)
    assert frame.stop == arrow.get(20)
    assert frame.tags == ['A', 'B', 'C']


def test_frames_from_sequence_of_lists(watson):
    test_frames = (
        ['0', 'project0',  0, 10],
        ['1', 'project1', 10, 20, ['A', 'B', 'C']]
    )
    watson.frames = test_frames

    assert len(watson.frames) == 2
    assert isinstance(watson.frames, Frames)

    frame = watson.frames.get_by_index(0)
    assert isinstance(frame, Frame)
    assert frame.id == '0'
    assert frame.project == 'project0'
    assert frame.start == arrow.get(0)
    assert frame.stop == arrow.get(10)

    frame = watson.frames.get_by_index(1)
    assert isinstance(frame, Frame)
    assert frame.id == '1'
    assert frame.project == 'project1'
    assert frame.start == arrow.get(10)
    assert frame.stop == arrow.get(20)
    assert frame.tags == ['A', 'B', 'C']


def test_frames_from_old_format(watson):
    test_frames = (
        [0, 10, 'project0', '0'],
        [10, 20, 'project1', '1', ['A', 'B', 'C']],
        [20, 30, 'project2', '2', ['D', 'E', 'F'], 30]
    )
    watson.frames = test_frames

    assert len(watson.frames) == 3
    assert isinstance(watson.frames, Frames)

    frame = watson.frames.get_by_index(0)
    assert isinstance(frame, Frame)
    assert frame.id == '0'
    assert frame.project == 'project0'
    assert frame.start == arrow.get(0)
    assert frame.stop == arrow.get(10)

    frame = watson.frames.get_by_index(1)
    assert isinstance(frame, Frame)
    assert frame.id == '1'
    assert frame.project == 'project1'
    assert frame.start == arrow.get(10)
    assert frame.stop == arrow.get(20)
    assert frame.tags == ['A', 'B', 'C']

    frame = watson.frames.get_by_index(2)
    assert isinstance(frame, Frame)
    assert frame.id == '2'
    assert frame.project == 'project2'
    assert frame.start == arrow.get(20)
    assert frame.stop == arrow.get(30)
    assert frame.tags == ['D', 'E', 'F']
    assert frame.updated_at == arrow.get(30)


def test_frames_from_frames(watson):
    frames_instance = Frames((
        ('0', 'project0',  0, 10),
        ('1', 'project1', 10, 20, ['A', 'B', 'C'])
    ))
    watson.frames = frames_instance

    assert len(watson.frames) == 2
    assert isinstance(watson.frames, Frames)
    assert watson.frames is frames_instance


def test_frames_get_by_index(watson):
    test_frames = (
        ('0', ('project0',  0, 10)),
        ('1', ('project1', 10, 20)),
        ('2', ('project2', 20, 30)),
        ('3', ('project3', 30, 40)),
        ('4', ('project4', 40, 50))
    )

    for id, frame in test_frames[:-1]:
        watson.frames[id] = frame

    assert len(watson.frames) == 4
    assert watson.frames.get_by_index(0).id == '0'
    assert watson.frames.get_by_index(0).project == 'project0'
    assert watson.frames.get_by_index(2).id == '2'
    assert watson.frames.get_by_index(2).project == 'project2'
    assert watson.frames.get_by_index(-1).id == '3'
    assert watson.frames.get_by_index(-1).project == 'project3'

    # adding an item
    id, frame = test_frames[-1]
    watson.frames[id] = frame
    assert len(watson.frames) == 5
    assert watson.frames.get_by_index(3).id == '3'
    assert watson.frames.get_by_index(-1).id == '4'

    # setting an existing item
    assert watson.frames.get_by_index(2).project == 'project2'
    watson.frames['2'] = ('project6', 50, 60)
    assert len(watson.frames) == 5
    assert watson.frames.get_by_index(2).project == 'project6'

    # deleting an item
    del watson.frames['2']
    assert len(watson.frames) == 4
    assert watson.frames.get_by_index(2).id == '3'
    assert watson.frames.get_by_index(2).project == 'project3'

    # index out of range
    with pytest.raises(IndexError):
        watson.frames.get_by_index(4)

    if not PY2:
        # move_to_end
        assert watson.frames.get_by_index(0).project == 'project0'
        watson.frames.move_to_end('0')
        assert watson.frames.get_by_index(-1).project == 'project0'

        assert watson.frames.get_by_index(0).project == 'project1'
        watson.frames.move_to_end('4', False)
        assert watson.frames.get_by_index(0).project == 'project4'


def test_frames_get_by_id(watson):
    test_frames = (
        ('abcdef', ('project0',  0, 10)),
        ('abcxyz', ('project1', 10, 20)),
        ('defghi', ('project2', 20, 30)),
    )

    for id, frame in test_frames:
        watson.frames[id] = frame

    frame = watson.frames['abcdef']
    assert frame.project == 'project0'
    frame = watson.frames['abcxyz']
    assert frame.project == 'project1'

    frame = watson.frames['abc']
    assert frame.project == 'project0'
    frame = watson.frames['def']
    assert frame.project == 'project2'


def test_frames_without_tags(watson):
    content = json.dumps([['abcdefg', 'foo', 0, 10]])

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 1
        frame = watson.frames['abcdefg']
        assert frame.id == 'abcdefg'
        assert frame.project == 'foo'
        assert frame.start == arrow.get(0)
        assert frame.stop == arrow.get(10)
        assert frame.tags == []


def test_frames_with_empty_file(watson):
    with mock.patch('%s.open' % builtins, mock.mock_open(read_data="")):
        with mock.patch('os.path.getsize', return_value=0):
            assert len(watson.frames) == 0


def test_frames_with_nonexistent_file(watson):
    with mock.patch('%s.open' % builtins, side_effect=IOError):
        assert len(watson.frames) == 0


def test_frames_watson_non_valid_json(watson):
    content = "{'foo': bar}"

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        with mock.patch('os.path.getsize') as mock_getsize:
            mock_getsize.return_value(len(content))
            with pytest.raises(WatsonError):
                watson.frames


def test_given_frames(config_dir):
    content = json.dumps([['abcdefg', 'foo', 0, 10, ['A']]])
    watson = Watson(frames=[['abcdefg', 'bar', 0, 10, ['A', 'B']]],
                    config_dir=config_dir)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 1
        frame = watson.frames['abcdefg']
        assert frame.project == 'bar'
        assert frame.tags == ['A', 'B']


def test_frames_with_empty_given_state(config_dir):
    content = json.dumps([['abcdefg', 'foo', 0, 10, ['A']]])
    watson = Watson(frames=[], config_dir=config_dir)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 0


# config

def test_empty_config_dir():
    watson = Watson()
    assert watson._dir == get_app_dir('watson')


def test_wrong_config(watson):
    content = u"""
toto
    """
    with mock.patch.object(ConfigParser, 'read', mock_read(content)):
        with pytest.raises(ConfigurationError):
            watson.config


def test_empty_config(watson):
    with mock.patch.object(ConfigParser, 'read', mock_read(u'')):
        assert len(watson.config.sections()) == 0


def test_config_get(watson):
    content = u"""
[backend]
url = foo
token =
    """
    with mock.patch.object(ConfigParser, 'read', mock_read(content)):
        config = watson.config
        assert config.get('backend', 'url') == 'foo'
        assert config.get('backend', 'token') == ''
        assert config.get('backend', 'foo') is None
        assert config.get('backend', 'foo', 'bar') == 'bar'
        assert config.get('option', 'spamm') is None
        assert config.get('option', 'spamm', 'eggs') == 'eggs'


def test_config_getboolean(watson):
    content = u"""
[options]
flag1 = 1
flag2 = ON
flag3 = True
flag4 = yes
flag5 = false
flag6 =
    """
    with mock.patch.object(ConfigParser, 'read', mock_read(content)):
        config = watson.config
        assert config.getboolean('options', 'flag1') is True
        assert config.getboolean('options', 'flag1', False) is True
        assert config.getboolean('options', 'flag2') is True
        assert config.getboolean('options', 'flag3') is True
        assert config.getboolean('options', 'flag4') is True
        assert config.getboolean('options', 'flag5') is False
        assert config.getboolean('options', 'flag6') is False
        assert config.getboolean('options', 'flag6', True) is True
        assert config.getboolean('options', 'missing') is False
        assert config.getboolean('options', 'missing', True) is True


def test_config_getint(watson):
    content = u"""
[options]
value1 = 42
value2 = spamm
value3 =
    """
    with mock.patch.object(ConfigParser, 'read', mock_read(content)):
        config = watson.config
        assert config.getint('options', 'value1') == 42
        assert config.getint('options', 'value1', 666) == 42
        assert config.getint('options', 'missing') is None
        assert config.getint('options', 'missing', 23) == 23
        # default is not converted!
        assert config.getint('options', 'missing', '42') == '42'
        assert config.getint('options', 'missing', 6.66) == 6.66

        with pytest.raises(ValueError):
            config.getint('options', 'value2')

        with pytest.raises(ValueError):
            config.getint('options', 'value3')


def test_config_getfloat(watson):
    content = u"""
[options]
value1 = 3.14
value2 = 42
value3 = spamm
value4 =
    """

    with mock.patch.object(ConfigParser, 'read', mock_read(content)):
        config = watson.config
        assert config.getfloat('options', 'value1') == 3.14
        assert config.getfloat('options', 'value1', 6.66) == 3.14
        assert config.getfloat('options', 'value2') == 42.0
        assert isinstance(config.getfloat('options', 'value2'), float)
        assert config.getfloat('options', 'missing') is None
        assert config.getfloat('options', 'missing', 3.14) == 3.14
        # default is not converted!
        assert config.getfloat('options', 'missing', '3.14') == '3.14'

        with pytest.raises(ValueError):
            config.getfloat('options', 'value3')

        with pytest.raises(ValueError):
            config.getfloat('options', 'value4')


def test_config_getlist(watson):
    content = u"""
# empty lines in option values (including the first one) are discarded
[options]
value1 =
    one

    two three
    four
    five six
# multiple inner space preserved
value2 = one  "two three" four 'five  six'
value3 = one
    two  three
# outer space stripped
value4 = one
     two three
    four
# hash char not at start of line does not start comment
value5 = one
   two #three
   four # five
"""
    with mock.patch.object(ConfigParser, 'read', mock_read(content)):
        gl = watson.config.getlist
        assert gl('options', 'value1') == ['one', 'two three', 'four',
                                           'five six']
        assert gl('options', 'value2') == ['one', 'two three', 'four',
                                           'five  six']
        assert gl('options', 'value3') == ['one', 'two  three']
        assert gl('options', 'value4') == ['one', 'two three', 'four']
        assert gl('options', 'value5') == ['one', 'two #three', 'four # five']

        # default values
        assert gl('options', 'novalue') == []
        assert gl('options', 'novalue', None) == []
        assert gl('options', 'novalue', 42) == 42
        assert gl('nosection', 'dummy') == []
        assert gl('nosection', 'dummy', None) == []
        assert gl('nosection', 'dummy', 42) == 42

        default = gl('nosection', 'dummy')
        default.append(42)
        assert gl('nosection', 'dummy') != [42], (
            "Modifying default return value should not have side effect.")


def test_set_config(watson):
    config = ConfigParser()
    config.set('foo', 'bar', 'lol')
    watson.config = config

    watson.config.get('foo', 'bar') == 'lol'


# start

def test_start_new_project(watson):
    watson.start('foo', ['A', 'B'])

    assert watson.current != {}
    assert watson.is_started is True
    assert watson.current.get('project') == 'foo'
    assert isinstance(watson.current.get('start'), arrow.Arrow)
    assert watson.current.get('tags') == ['A', 'B']


def test_start_new_project_without_tags(watson):
    watson.start('foo')

    assert watson.current != {}
    assert watson.is_started is True
    assert watson.current.get('project') == 'foo'
    assert isinstance(watson.current.get('start'), arrow.Arrow)
    assert watson.current.get('tags') == []


def test_start_two_projects(watson):
    watson.start('foo')

    with pytest.raises(WatsonError):
        watson.start('bar')

    assert watson.current != {}
    assert watson.current['project'] == 'foo'
    assert watson.is_started is True


# stop

def test_stop_started_project(watson):
    watson.start('foo', tags=['A', 'B'])
    watson.stop()

    assert watson.current == {}
    assert watson.is_started is False
    assert len(watson.frames) == 1
    frame = watson.frames.get_by_index(0)
    assert frame.project == 'foo'
    assert isinstance(frame.start, arrow.Arrow)
    assert isinstance(frame.stop, arrow.Arrow)
    assert frame.tags == ['A', 'B']


def test_stop_started_project_without_tags(watson):
    watson.start('foo')
    watson.stop()

    assert watson.current == {}
    assert watson.is_started is False
    assert len(watson.frames) == 1
    frame = watson.frames.get_by_index(0)
    assert frame.project == 'foo'
    assert isinstance(frame.start, arrow.Arrow)
    assert isinstance(frame.stop, arrow.Arrow)
    assert frame.tags == []


def test_stop_no_project(watson):
    with pytest.raises(WatsonError):
        watson.stop()


# cancel

def test_cancel_started_project(watson):
    watson.start('foo')
    watson.cancel()

    assert watson.current == {}
    assert len(watson.frames) == 0


def test_cancel_no_project(watson):
    with pytest.raises(WatsonError):
        watson.cancel()


# save

def test_save_without_changes(watson):
    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert not json_mock.called


def test_save_current(watson):
    watson.start('foo', ['A', 'B'])

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert result['project'] == 'foo'
            assert isinstance(result['start'], (int, float))
            assert result['tags'] == ['A', 'B']


def test_save_current_without_tags(watson):
    watson.start('foo')

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert result['project'] == 'foo'
            assert isinstance(result['start'], (int, float))
            assert result['tags'] == []

            dump_args = json_mock.call_args[1]
            assert dump_args['ensure_ascii'] is False


def test_save_empty_current(config_dir):
    watson = Watson(current={'project': 'foo', 'start': 0},
                    config_dir=config_dir)
    watson.current = {}

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert result == {}


def test_save_frames_no_change(config_dir):
    watson = Watson(frames=[['abcdefg', 'foo', 0, 10]],
                    config_dir=config_dir)

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert not json_mock.called


def test_save_added_frame(config_dir):
    watson = Watson(frames=[['abcdefg', 'foo', 0, 10]], config_dir=config_dir)
    watson.frames.add('bar', 10, 20, tags=['A'])

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert len(result) == 2
            assert result[0][0] == 'abcdefg'
            assert result[0][1] == 'foo'
            assert result[0][2] == 0
            assert result[0][3] == 10
            assert result[0][4] == []
            assert result[1][1] == 'bar'
            assert result[1][2] == 10
            assert result[1][3] == 20
            assert result[1][4] == ['A']


def test_save_changed_frame(config_dir):
    watson = Watson(frames=[['abcdefg', 'foo', 0, 10, ['A']]],
                    config_dir=config_dir)
    watson.frames['abcdefg'] = ('bar', 0, 10, ['A', 'B'])

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert len(result) == 1
            assert result[0][0] == 'abcdefg'
            assert result[0][1] == 'bar'
            assert result[0][2] == 0
            assert result[0][3] == 10
            assert result[0][4] == ['A', 'B']

            dump_args = json_mock.call_args[1]
            assert dump_args['ensure_ascii'] is False


def test_save_config_no_changes(watson):
    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch.object(ConfigParser, 'write') as write_mock:
            watson.save()

            assert not write_mock.called


def test_save_config(watson):
    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch.object(ConfigParser, 'write') as write_mock:
            watson.config = ConfigParser()
            watson.save()

            assert write_mock.call_count == 1


def test_save_last_sync(watson):
    now = arrow.now()
    watson.last_sync = now

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            assert json_mock.call_args[0][0] == now.timestamp


def test_save_empty_last_sync(config_dir):
    watson = Watson(last_sync=arrow.now(), config_dir=config_dir)
    watson.last_sync = None

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            assert json_mock.call_args[0][0] == 0


def test_watson_save_calls_safe_save(watson, config_dir):
    frames_file = os.path.join(config_dir, 'frames')
    watson.start('foo', tags=['A', 'B'])
    watson.stop()

    with mock.patch('watson.watson.safe_save') as save_mock:
        watson.save()

        assert watson._frames.changed
        assert save_mock.call_count == 1
        assert len(save_mock.call_args[0]) == 2
        assert save_mock.call_args[0][0] == frames_file


# push

def test_push_with_no_config(watson):
    config = ConfigParser()
    watson.config = config

    with pytest.raises(WatsonError):
        watson.push(arrow.now())


def test_push_with_no_url(watson):
    config = ConfigParser()
    config.add_section('backend')
    config.set('backend', 'token', 'bar')
    watson.config = config

    with pytest.raises(WatsonError):
        watson.push(arrow.now())


def test_push_with_no_token(watson):
    config = ConfigParser()
    config.add_section('backend')
    config.set('backend', 'url', 'http://foo.com')
    watson.config = config

    with pytest.raises(WatsonError):
        watson.push(arrow.now())


def test_push(watson, monkeypatch):
    config = ConfigParser()
    config.add_section('backend')
    config.set('backend', 'url', 'http://foo.com')
    config.set('backend', 'token', 'bar')

    watson.frames.add('foo', 1, 2)
    watson.frames.add('foo', 3, 4)

    watson.last_sync = arrow.now()

    watson.frames.add('bar', 1, 2, ['A', 'B'])
    watson.frames.add('lol', 1, 2)

    last_pull = arrow.now()

    watson.frames.add('foo', 1, 2)
    watson.frames.add('bar', 3, 4)

    monkeypatch.setattr(watson, '_get_remote_projects', lambda *args: [
        {'name': 'foo', 'url': '/projects/1/'},
        {'name': 'bar', 'url': '/projects/2/'},
        {'name': 'lol', 'url': '/projects/3/'},
    ])

    class Response:
        def __init__(self):
            self.status_code = 201

    with mock.patch('requests.post') as mock_put:
        mock_put.return_value = Response()

        with mock.patch.object(
                Watson, 'config', new_callable=mock.PropertyMock
                ) as mock_config:
            mock_config.return_value = config
            watson.push(last_pull)

        requests.post.assert_called_once_with(
            mock.ANY,
            mock.ANY,
            headers={
                'content-type': 'application/json',
                'Authorization': "Token " + config.get('backend', 'token')
            }
        )

        frames_sent = json.loads(mock_put.call_args[0][1])
        assert len(frames_sent) == 2

        assert frames_sent[0].get('project') == '/projects/2/'
        assert frames_sent[0].get('tags') == ['A', 'B']

        assert frames_sent[1].get('project') == '/projects/3/'
        assert frames_sent[1].get('tags') == []


# pull

def test_pull_with_no_config(watson):
    config = ConfigParser()
    watson.config = config

    with pytest.raises(ConfigurationError):
        watson.pull()


def test_pull_with_no_url(watson):
    config = ConfigParser()
    config.add_section('backend')
    config.set('backend', 'token', 'bar')
    watson.config = config

    with pytest.raises(ConfigurationError):
        watson.pull()


def test_pull_with_no_token(watson):
    config = ConfigParser()
    config.add_section('backend')
    config.set('backend', 'url', 'http://foo.com')
    watson.config = config

    with pytest.raises(ConfigurationError):
        watson.pull()


def test_pull(watson, monkeypatch):
    config = ConfigParser()
    config.add_section('backend')
    config.set('backend', 'url', 'http://foo.com')
    config.set('backend', 'token', 'bar')

    watson.last_sync = arrow.now()

    watson.frames.add('foo', 1, 2, ['A', 'B'], id='1')

    monkeypatch.setattr(watson, '_get_remote_projects', lambda *args: [
        {'name': 'foo', 'url': '/projects/1/'},
        {'name': 'bar', 'url': '/projects/2/'},
    ])

    class Response:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return [
                {'project': '/projects/1/', 'start': 3, 'stop': 4, 'id': '1',
                 'tags': ['A']},
                {'project': '/projects/2/', 'start': 4, 'stop': 5, 'id': '2',
                 'tags': []}
            ]

    with mock.patch('requests.get') as mock_get:
        mock_get.return_value = Response()

        with mock.patch.object(
                Watson, 'config', new_callable=mock.PropertyMock
                ) as mock_config:
            mock_config.return_value = config
            watson.pull()

        requests.get.assert_called_once_with(
            mock.ANY,
            params={'last_sync': watson.last_sync},
            headers={
                'content-type': 'application/json',
                'Authorization': "Token " + config.get('backend', 'token')
            }
        )

    assert len(watson.frames) == 2

    frame = watson.frames.get_by_index(0)
    assert frame.id == '1'
    assert frame.project == 'foo'
    assert frame.start.timestamp == 3
    assert frame.stop.timestamp == 4
    assert frame.tags == ['A']

    frame = watson.frames.get_by_index(1)
    assert frame.id == '2'
    assert frame.project == 'bar'
    assert frame.start.timestamp == 4
    assert frame.stop.timestamp == 5
    assert frame.tags == []


# projects

def test_projects(watson):
    for name in ('foo', 'bar', 'bar', 'bar', 'foo', 'lol'):
        watson.frames.add(name, 0, 0)

    assert watson.projects == ['bar', 'foo', 'lol']


def test_projects_no_frames(watson):
    assert watson.projects == []


# tags

def test_tags(watson):
    samples = (
        ('foo', ('A', 'D')),
        ('bar', ('A', 'C')),
        ('foo', ('B', 'C')),
        ('lol', ()),
        ('bar', ('C'))
    )

    for name, tags in samples:
        watson.frames.add(name, 0, 0, tags)

    assert watson.tags == ['A', 'B', 'C', 'D']


def test_tags_no_frames(watson):
    assert watson.tags == []


# merge

@pytest.mark.datafiles(
    TEST_FIXTURE_DIR / 'frames-with-conflict',
    )
def test_merge_report(watson, datafiles):
    # Get report
    watson.frames.add('foo', 0, 15, id='1', updated_at=15)
    watson.frames.add('bar', 20, 45, id='2', updated_at=45)

    conflicting, merging = watson.merge_report(
        str(datafiles) + '/frames-with-conflict')

    assert len(conflicting) == 1
    assert len(merging) == 1

    assert conflicting[0].id == '2'
    assert merging[0].id == '3'


# report/log

_dt = datetime.datetime
_tz = {'tzinfo': tzutc()}


@pytest.mark.parametrize('now, mode, start_time', [
    (_dt(2016, 6, 2, **_tz), 'year', _dt(2016, 1, 1, **_tz)),
    (_dt(2016, 6, 2, **_tz), 'month', _dt(2016, 6, 1, **_tz)),
    (_dt(2016, 6, 2, **_tz), 'week', _dt(2016, 5, 30, **_tz)),
    (_dt(2016, 6, 2, **_tz), 'day', _dt(2016, 6, 2, **_tz)),

    (_dt(2012, 2, 24, **_tz), 'year', _dt(2012, 1, 1, **_tz)),
    (_dt(2012, 2, 24, **_tz), 'month', _dt(2012, 2, 1, **_tz)),
    (_dt(2012, 2, 24, **_tz), 'week', _dt(2012, 2, 20, **_tz)),
    (_dt(2012, 2, 24, **_tz), 'day', _dt(2012, 2, 24, **_tz)),
])
def test_get_start_time_for_period(now, mode, start_time):
    with mock_datetime(now, datetime):
        assert get_start_time_for_period(mode).datetime == start_time


# utils

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
