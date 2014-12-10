import sys
import json

try:
    from unittest import mock
except ImportError:
    import mock

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

import pytest
import requests
import arrow

from watson import Watson, WatsonError
from watson.watson import ConfigParser

PY2 = sys.version_info[0] == 2

if not PY2:
    builtins = 'builtins'
else:
    builtins = '__builtin__'


@pytest.fixture
def watson():
    return Watson(current={}, frames=[])


# current

def test_current():
    watson = Watson()

    content = json.dumps({'project': 'foo', 'start': 0})

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.current['project'] == 'foo'
        assert watson.current['start'] == arrow.get(0)


def test_current_with_empty_file():
    watson = Watson()

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data="")):
        with mock.patch('os.path.getsize', return_value=0):
            assert watson.current == {}


def test_current_with_nonexistent_file():
    watson = Watson()

    with mock.patch('%s.open' % builtins, side_effect=IOError):
        assert watson.current == {}


def test_current_watson_non_valid_json():
    watson = Watson()

    content = "{'foo': bar}"

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        with pytest.raises(WatsonError):
            watson.current


def test_current_with_given_state():
    content = json.dumps({'project': 'foo', 'start': 0})
    watson = Watson(current={'project': 'bar', 'start': 0})

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.current['project'] == 'bar'


def test_current_with_empty_given_state():
    content = json.dumps({'project': 'foo', 'start': 0})
    watson = Watson(current={})

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.current == {}


# frames

def test_frames():
    watson = Watson()

    content = json.dumps([[0, 10, 'foo', None]])

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 1
        assert watson.frames[0].project == 'foo'
        assert watson.frames[0].start == arrow.get(0)
        assert watson.frames[0].stop == arrow.get(10)


def test_frames_with_empty_file():
    watson = Watson()

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data="")):
        with mock.patch('os.path.getsize', return_value=0):
            assert len(watson.frames) == 0


def test_frames_with_nonexistent_file():
    watson = Watson()

    with mock.patch('%s.open' % builtins, side_effect=IOError):
        assert len(watson.frames) == 0


def test_frames_watson_non_valid_json():
    watson = Watson()

    content = "{'foo': bar}"

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        with pytest.raises(WatsonError):
            watson.frames


def test_given_frames():
    content = json.dumps([[0, 10, 'foo', None]])
    watson = Watson(frames=[[0, 10, 'bar', None]])

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 1
        assert watson.frames[0].project == 'bar'


def test_frames_with_empty_given_state():
    content = json.dumps([[0, 10, 'foo', None]])
    watson = Watson(frames=[])

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 0


# config

def test_config(watson):
    content = u"""
[crick]
url = foo
token = bar
    """
    mocked_read = lambda self, name: self._read(StringIO(content), name)
    with mock.patch.object(ConfigParser, 'read', mocked_read):
        config = watson.config
        assert config.get('crick', 'url') == 'foo'
        assert config.get('crick', 'token') == 'bar'


def test_config_without_url(watson):
    content = u"""
[crick]
token = bar
    """
    mocked_read = lambda self, name: self._read(StringIO(content), name)
    with mock.patch.object(ConfigParser, 'read', mocked_read):
        with pytest.raises(WatsonError):
            watson.config


def test_config_without_token(watson):
    content = u"""
[crick]
token = bar
    """
    mocked_read = lambda self, name: self._read(StringIO(content), name)
    with mock.patch.object(ConfigParser, 'read', mocked_read):
        with pytest.raises(WatsonError):
            watson.config


def test_no_config(watson):
    with mock.patch('%s.open' % builtins, side_effect=IOError):
        with pytest.raises(WatsonError):
            watson.config


# start

def test_start_new_project(watson):
    watson.start('foo')

    assert watson.current != {}
    assert watson.is_started is True
    assert watson.current.get('project') == 'foo'
    assert isinstance(watson.current.get('start'), arrow.Arrow)


def test_start_new_subprojects(watson):
    watson.start('foo/bar/lol')

    assert watson.current != {}
    assert watson.is_started is True
    assert watson.current.get('project') == 'foo/bar/lol'


def test_start_two_projects(watson):
    watson.start('foo')

    with pytest.raises(WatsonError):
        watson.start('bar')

    assert watson.current != {}
    assert watson.current['project'] == 'foo'
    assert watson.is_started is True


# stop

def test_stop_started_project(watson):
    watson.start('foo')
    watson.stop()

    assert watson.current == {}
    assert watson.is_started is False
    assert len(watson.frames) == 1
    assert watson.frames[0].project == 'foo'
    assert isinstance(watson.frames[0].start, arrow.Arrow)
    assert isinstance(watson.frames[0].stop, arrow.Arrow)


def test_stop_started_subproject(watson):
    watson.start('foo/bar/lol')
    watson.stop()

    assert watson.current == {}
    assert watson.is_started is False
    assert len(watson.frames) == 1
    assert watson.frames[0].project == 'foo/bar/lol'
    assert isinstance(watson.frames[0].start, arrow.Arrow)
    assert isinstance(watson.frames[0].stop, arrow.Arrow)


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
    watson.start('foo')

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert result['project'] == 'foo'
            assert isinstance(result['start'], (int, float))


def test_save_empty_current():
    watson = Watson(current={'project': 'foo', 'start': 0})
    watson.current = {}

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert result == {}


def test_save_frames_no_change():
    watson = Watson(frames=[[0, 10, 'foo', None]])

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert not json_mock.called


def test_save_added_frame():
    watson = Watson(frames=[[0, 10, 'foo', None]])
    watson.frames.add('bar', 10, 20)

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert len(result) == 2
            assert result[0][2] == 'foo'
            assert result[1][2] == 'bar'


def test_save_changed_frame():
    watson = Watson(frames=[[0, 10, 'foo', None]])
    watson.frames[0] = ('bar', 0, 10)

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert len(result) == 1
            assert result[0][2] == 'bar'


# push

@pytest.fixture
def frames():
    return [
        [0, 0, 'foo', None],
        [0, 0, 'foo', 42],
        [0, 0, 'bar', None],
        [0, 0, 'foo/x', None],
        [0, 0, 'foo/x', 43],
        [0, 0, 'foo/x/y', None],
        [0, 0, 'foo/z', 44],
        [0, 0, 'bar', None],
        [0, 0, 'bar', 45],
    ]


def test_push(frames):
    watson = Watson(frames=frames)

    config = ConfigParser()
    config.add_section('crick')
    config.set('crick', 'url', 'http://foo.com')
    config.set('crick', 'token', 'bar')

    class Response:
        def __init__(self):
            self.status_code = 201

        def json(self):
            return list(range(5))

    with mock.patch('requests.post') as mock_post:
        mock_post.return_value = Response()

        with mock.patch.object(
                Watson, 'config', new_callable=mock.PropertyMock
                ) as mock_config:
            mock_config.return_value = config
            watson.push()

        requests.post.assert_called_once_with(
            config.get('crick', 'url') + '/frames/',
            mock.ANY,
            headers={
                'content-type': 'application/json',
                'Authorization': "Token " + config.get('crick', 'token')
            }
        )

        frames_received = json.loads(mock_post.call_args[0][1])['frames']
        assert len(frames_received) == 5

    assert all(frame.id is not None for frame in watson.frames)

    assert watson.frames[0].id == 0
    assert watson.frames[0].project == 'foo'
    assert watson.frames[1].id == 42
    assert watson.frames[1].project == 'foo'
    assert watson.frames[2].id == 1
    assert watson.frames[2].project == 'bar'
    assert watson.frames[3].id == 2
    assert watson.frames[3].project == 'foo/x'
    assert watson.frames[4].id == 43
    assert watson.frames[4].project == 'foo/x'
    assert watson.frames[5].id == 3
    assert watson.frames[5].project == 'foo/x/y'
    assert watson.frames[6].id == 44
    assert watson.frames[6].project == 'foo/z'
    assert watson.frames[7].id == 4
    assert watson.frames[7].project == 'bar'
    assert watson.frames[8].id == 45
    assert watson.frames[8].project == 'bar'


def test_push_force(frames):
    watson = Watson(frames=frames)

    config = ConfigParser()
    config.add_section('crick')
    config.set('crick', 'url', 'http://foo.com')
    config.set('crick', 'token', 'bar')

    class PutResponse:
        def __init__(self):
            self.status_code = 200

    class PostResponse:
        def __init__(self):
            self.status_code = 201

        def json(self):
            return list(range(4))

    with mock.patch('requests.put') as mock_put:
        with mock.patch('requests.post') as mock_post:
            mock_put.return_value = PutResponse()
            mock_post.return_value = PostResponse()

            with mock.patch.object(
                    Watson, 'config', new_callable=mock.PropertyMock
                    ) as mock_config:
                mock_config.return_value = config
                watson.push(force=True)

            args = (config.get('crick', 'url') + '/frames/', mock.ANY)
            kwargs = {
                'headers': {
                    'content-type': 'application/json',
                    'Authorization': "Token " + config.get('crick', 'token')
                }
            }
            requests.post.assert_called_once_with(*args, **kwargs)
            requests.put.assert_called_once_with(*args, **kwargs)

            frames_sent = json.loads(mock_put.call_args[0][1])['frames']
            assert len(frames_sent) == 4
            assert [f['id'] for f in frames_sent] == [42, 43, 44, 45]


# projects

def test_projects(frames):
    watson = Watson(frames=frames)

    assert watson.projects == [
        'bar',
        'foo',
        'foo/x',
        'foo/x/y',
        'foo/z'
    ]


def test_projects_no_frames(watson):
    assert watson.projects == []
