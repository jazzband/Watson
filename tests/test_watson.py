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

    content = json.dumps({'project': 'foo', 'start': 0, 'tags': ['A', 'B']})

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.current['project'] == 'foo'
        assert watson.current['start'] == arrow.get(0)
        assert watson.current['tags'] == ['A', 'B']


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
        with mock.patch('os.path.getsize', return_value=len(content)):
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


# last_sync

def test_last_sync():
    watson = Watson()

    now = arrow.get(123)
    content = json.dumps(now.timestamp)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.last_sync == now


def test_last_sync_with_empty_file():
    watson = Watson()

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data="")):
        with mock.patch('os.path.getsize', return_value=0):
            assert watson.last_sync == arrow.get(0)


def test_last_sync_with_nonexistent_file():
    watson = Watson()

    with mock.patch('%s.open' % builtins, side_effect=IOError):
        assert watson.last_sync == arrow.get(0)


def test_last_sync_watson_non_valid_json():
    watson = Watson()

    content = "{'foo': bar}"

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        with mock.patch('os.path.getsize', return_value=len(content)):
            with pytest.raises(WatsonError):
                watson.last_sync


def test_last_sync_with_given_state():
    content = json.dumps(123)
    now = arrow.now()
    watson = Watson(last_sync=now)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.last_sync == now


def test_last_sync_with_empty_given_state():
    content = json.dumps(123)
    watson = Watson(last_sync=None)

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert watson.last_sync == arrow.get(0)


# frames

def test_frames():
    watson = Watson()

    content = json.dumps([[0, 10, 'foo', None, ['A', 'B', 'C']]])

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 1
        assert watson.frames[0].project == 'foo'
        assert watson.frames[0].start == arrow.get(0)
        assert watson.frames[0].stop == arrow.get(10)
        assert watson.frames[0].tags == ['A', 'B', 'C']


def test_frames_without_tags():
    watson = Watson()

    content = json.dumps([[0, 10, 'foo', None]])

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 1
        assert watson.frames[0].project == 'foo'
        assert watson.frames[0].start == arrow.get(0)
        assert watson.frames[0].stop == arrow.get(10)
        assert watson.frames[0].tags == []


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
    content = json.dumps([[0, 10, 'foo', None, ['A']]])
    watson = Watson(frames=[[0, 10, 'bar', None, ['A', 'B']]])

    with mock.patch('%s.open' % builtins, mock.mock_open(read_data=content)):
        assert len(watson.frames) == 1
        assert watson.frames[0].project == 'bar'
        assert watson.frames[0].tags == ['A', 'B']


def test_frames_with_empty_given_state():
    content = json.dumps([[0, 10, 'foo', None, ['A']]])
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


def test_wrong_config(watson):
    content = u"""
toto
    """
    mocked_read = lambda self, name: self._read(StringIO(content), name)
    with mock.patch.object(ConfigParser, 'read', mocked_read):
        with pytest.raises(WatsonError):
            watson.config


def test_empty_config(watson):
    mocked_read = lambda self, name: self._read(StringIO(''), name)
    with mock.patch.object(ConfigParser, 'read', mocked_read):
        assert watson.config == ConfigParser()


def test_set_config(watson):
    config = ConfigParser()
    config.add_section('foo')
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
    assert watson.frames[0].project == 'foo'
    assert isinstance(watson.frames[0].start, arrow.Arrow)
    assert isinstance(watson.frames[0].stop, arrow.Arrow)
    assert watson.frames[0].tags == ['A', 'B']


def test_stop_started_project_without_tags(watson):
    watson.start('foo')
    watson.stop()

    assert watson.current == {}
    assert watson.is_started is False
    assert len(watson.frames) == 1
    assert watson.frames[0].project == 'foo'
    assert isinstance(watson.frames[0].start, arrow.Arrow)
    assert isinstance(watson.frames[0].stop, arrow.Arrow)
    assert watson.frames[0].tags == []


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
    watson.frames.add('bar', 10, 20, ['A'])

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert len(result) == 2
            assert result[0][2] == 'foo'
            assert result[0][4] == []
            assert result[1][2] == 'bar'
            assert result[1][4] == ['A']


def test_save_changed_frame():
    watson = Watson(frames=[[0, 10, 'foo', None, ['A']]])
    watson.frames[0] = ('bar', 0, 10, ['A', 'B'])

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            result = json_mock.call_args[0][0]
            assert len(result) == 1
            assert result[0][2] == 'bar'
            assert result[0][4] == ['A', 'B']


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


def test_save_empty_last_sync():
    watson = Watson(last_sync=arrow.now())
    watson.last_sync = None

    with mock.patch('%s.open' % builtins, mock.mock_open()):
        with mock.patch('json.dump') as json_mock:
            watson.save()

            assert json_mock.call_count == 1
            assert json_mock.call_args[0][0] == 0


# push

def test_push_with_no_config(watson):
    config = ConfigParser()
    watson.config = config

    with pytest.raises(WatsonError):
        watson.push(arrow.now())


def test_push_with_no_url(watson):
    config = ConfigParser()
    config.add_section('crick')
    config.set('crick', 'token', 'bar')
    watson.config = config

    with pytest.raises(WatsonError):
        watson.push(arrow.now())


def test_push_with_no_token(watson):
    config = ConfigParser()
    config.add_section('crick')
    config.set('crick', 'url', 'http://foo.com')
    watson.config = config

    with pytest.raises(WatsonError):
        watson.push(arrow.now())


def test_push(watson, monkeypatch):
    config = ConfigParser()
    config.add_section('crick')
    config.set('crick', 'url', 'http://foo.com')
    config.set('crick', 'token', 'bar')

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
                'Authorization': "Token " + config.get('crick', 'token')
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

    with pytest.raises(WatsonError):
        watson.pull()


def test_pull_with_no_url(watson):
    config = ConfigParser()
    config.add_section('crick')
    config.set('crick', 'token', 'bar')
    watson.config = config

    with pytest.raises(WatsonError):
        watson.pull()


def test_pull_with_no_token(watson):
    config = ConfigParser()
    config.add_section('crick')
    config.set('crick', 'url', 'http://foo.com')
    watson.config = config

    with pytest.raises(WatsonError):
        watson.pull()


def test_pull(watson, monkeypatch):
    config = ConfigParser()
    config.add_section('crick')
    config.set('crick', 'url', 'http://foo.com')
    config.set('crick', 'token', 'bar')

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
                'Authorization': "Token " + config.get('crick', 'token')
            }
        )

    assert len(watson.frames) == 2

    assert watson.frames[0].id == '1'
    assert watson.frames[0].project == 'foo'
    assert watson.frames[0].start.timestamp == 3
    assert watson.frames[0].stop.timestamp == 4
    assert watson.frames[0].tags == ['A']

    assert watson.frames[1].id == '2'
    assert watson.frames[1].project == 'bar'
    assert watson.frames[1].start.timestamp == 4
    assert watson.frames[1].stop.timestamp == 5
    assert watson.frames[1].tags == []


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
