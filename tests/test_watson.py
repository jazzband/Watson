"""Unit tests for the main 'watson' module."""

import json
import os

import arrow
from click import get_app_dir
import py
import pytest
import requests

from watson import Watson, WatsonError
from watson.watson import ConfigParser, ConfigurationError
from watson.utils import PY2

from . import mock_read

TEST_FIXTURE_DIR = py.path.local(
    os.path.dirname(
        os.path.realpath(__file__)
        )
    ) / 'resources'

if not PY2:
    builtins = 'builtins'
else:
    builtins = '__builtin__'


@pytest.fixture
def json_mock(mock):
    return mock.patch.object(
        json, 'dumps', side_effect=json.dumps, autospec=True
    )


# NOTE: All timestamps need to be > 3600 to avoid breaking the tests on
# Windows.

# current

def test_current(mock, watson):
    content = json.dumps({'project': 'foo', 'start': 4000, 'tags': ['A', 'B']})

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.current['project'] == 'foo'
    assert watson.current['start'] == arrow.get(4000)
    assert watson.current['tags'] == ['A', 'B']


def test_current_with_empty_file(mock, watson):
    mock.patch('%s.open' % builtins, mock.mock_open(read_data=""))
    mock.patch('os.path.getsize', return_value=0)
    assert watson.current == {}


def test_current_with_nonexistent_file(mock, watson):
    mock.patch('%s.open' % builtins, side_effect=IOError)
    assert watson.current == {}


def test_current_watson_non_valid_json(mock, watson):
    content = "{'foo': bar}"

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    mock.patch('os.path.getsize', return_value=len(content))
    with pytest.raises(WatsonError):
        watson.current


def test_current_with_given_state(config_dir, mock):
    content = json.dumps({'project': 'foo', 'start': 4000})
    watson = Watson(current={'project': 'bar', 'start': 4000},
                    config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.current['project'] == 'bar'


def test_current_with_empty_given_state(config_dir, mock):
    content = json.dumps({'project': 'foo', 'start': 4000})
    watson = Watson(current=[], config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.current == {}


# last_sync

def test_last_sync(mock, watson):
    now = arrow.get(4123)
    content = json.dumps(now.timestamp)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.last_sync == now


def test_last_sync_with_empty_file(mock, watson):
    mock.patch('%s.open' % builtins, mock.mock_open(read_data=""))
    mock.patch('os.path.getsize', return_value=0)
    assert watson.last_sync == arrow.get(0)


def test_last_sync_with_nonexistent_file(mock, watson):
    mock.patch('%s.open' % builtins, side_effect=IOError)
    assert watson.last_sync == arrow.get(0)


def test_last_sync_watson_non_valid_json(mock, watson):
    content = "{'foo': bar}"

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    mock.patch('os.path.getsize', return_value=len(content))
    with pytest.raises(WatsonError):
        watson.last_sync


def test_last_sync_with_given_state(config_dir, mock):
    content = json.dumps(123)
    now = arrow.now()
    watson = Watson(last_sync=now, config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.last_sync == now


def test_last_sync_with_empty_given_state(config_dir, mock):
    content = json.dumps(123)
    watson = Watson(last_sync=None, config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.last_sync == arrow.get(0)


# frames

def test_frames(mock, watson):
    content = json.dumps([[4000, 4010, 'foo', None, ['A', 'B', 'C']]])

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert len(watson.frames) == 1
    assert watson.frames[0].project == 'foo'
    assert watson.frames[0].start == arrow.get(4000)
    assert watson.frames[0].stop == arrow.get(4010)
    assert watson.frames[0].tags == ['A', 'B', 'C']


def test_frames_without_tags(mock, watson):
    content = json.dumps([[4000, 4010, 'foo', None]])

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert len(watson.frames) == 1
    assert watson.frames[0].project == 'foo'
    assert watson.frames[0].start == arrow.get(4000)
    assert watson.frames[0].stop == arrow.get(4010)
    assert watson.frames[0].tags == []


def test_frames_with_message(mocker, watson):
    """Test loading frames with messages."""
    content = json.dumps([
        [3601, 3610, 'foo', 'abcdefg', ['A', 'B', 'C'], 3650,
         "My hovercraft is full of eels"]
    ])
    
    mocker.patch('%s.open' % builtins, mocker.mock_open(read_data=content))
    assert len(watson.frames) == 1
    frame = watson.frames['abcdefg']
    assert frame.id == 'abcdefg'
    assert frame.project == 'foo'
    assert frame.start == arrow.get(3601)
    assert frame.stop == arrow.get(3610)
    assert frame.tags == ['A', 'B', 'C']
    assert frame.message == "My hovercraft is full of eels"


def test_frames_without_message(mocker, watson):
    """Test loading frames without messages."""
    content = json.dumps([
        [3601, 3610, 'foo', 'abcdefg'],
        [3611, 3620, 'foo', 'hijklmn', ['A', 'B', 'C']],
        [3621, 3630, 'foo', 'opqrstu', ['A', 'B', 'C'], 3630]
    ])

    mocker.patch('%s.open' % builtins, mocker.mock_open(read_data=content))
    assert len(watson.frames) == 3
    frame = watson.frames['abcdefg']
    assert frame.id == 'abcdefg'
    assert frame.project == 'foo'
    assert frame.start == arrow.get(3601)
    assert frame.stop == arrow.get(3610)
    assert frame.tags == []
    assert frame.message is None

    frame = watson.frames['hijklmn']
    assert frame.id == 'hijklmn'
    assert frame.tags == ['A', 'B', 'C']
    assert frame.message is None

    frame = watson.frames['opqrstu']
    assert frame.id == 'opqrstu'
    assert frame.tags == ['A', 'B', 'C']
    assert frame.updated_at == arrow.get(3630)
    assert frame.message is None


def test_frames_with_empty_file(mock, watson):
    mock.patch('%s.open' % builtins, mock.mock_open(read_data=""))
    mock.patch('os.path.getsize', return_value=0)
    assert len(watson.frames) == 0


def test_frames_with_nonexistent_file(mock, watson):
    mock.patch('%s.open' % builtins, side_effect=IOError)
    assert len(watson.frames) == 0


def test_frames_watson_non_valid_json(mock, watson):
    content = "{'foo': bar}"

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    mock.patch('os.path.getsize', return_value=len(content))
    with pytest.raises(WatsonError):
        watson.frames


def test_given_frames(config_dir, mock):
    content = json.dumps([[4000, 4010, 'foo', None, ['A']]])
    watson = Watson(frames=[[4000, 4010, 'bar', None, ['A', 'B']]],
                    config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert len(watson.frames) == 1
    assert watson.frames[0].project == 'bar'
    assert watson.frames[0].tags == ['A', 'B']


def test_frames_with_empty_given_state(config_dir, mock):
    content = json.dumps([[0, 10, 'foo', None, ['A']]])
    watson = Watson(frames=[], config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert len(watson.frames) == 0


# config

def test_empty_config_dir():
    watson = Watson()
    assert watson._dir == get_app_dir('watson')


def test_wrong_config(mock, watson):
    content = u"""
toto
    """
    mock.patch.object(ConfigParser, 'read', mock_read(content))
    with pytest.raises(ConfigurationError):
        watson.config


def test_empty_config(mock, watson):
    mock.patch.object(ConfigParser, 'read', mock_read(u''))
    assert len(watson.config.sections()) == 0


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


def test_start_default_tags(mock, watson):
    content = u"""
[default_tags]
my project = A B
    """

    mock.patch.object(ConfigParser, 'read', mock_read(content))
    watson.start('my project')
    assert watson.current['tags'] == ['A', 'B']


def test_start_default_tags_with_supplementary_input_tags(mock, watson):
    content = u"""
[default_tags]
my project = A B
    """

    mock.patch.object(ConfigParser, 'read', mock_read(content))
    watson.start('my project', tags=['C', 'D'])
    assert watson.current['tags'] == ['C', 'D', 'A', 'B']


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


def test_stop_started_project_without_message(watson):
    """Test stopping watson without adding a message."""
    watson.start('foo')
    watson.stop()

    assert watson.current == {}
    assert watson.is_started is False
    assert len(watson.frames) == 1
    frame = watson.frames[0]
    assert frame.project == 'foo'
    assert frame.message is None


def test_stop_started_project_with_message(watson):
    watson.start('foo')
    watson._current['message'] = "My hovercraft is full of eels"
    watson.stop()

    assert watson.current == {}
    assert watson.is_started is False
    assert len(watson.frames) == 1
    frame = watson.frames.get_by_index(0)
    assert frame.project == 'foo'
    assert frame.message == "My hovercraft is full of eels"


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

def test_save_without_changes(mock, watson, json_mock):
    mock.patch('%s.open' % builtins, mock.mock_open())
    watson.save()

    assert not json_mock.called


def test_save_current(mock, watson, json_mock):
    watson.start('foo', ['A', 'B'])

    mock.patch('%s.open' % builtins, mock.mock_open())
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert result['project'] == 'foo'
    assert isinstance(result['start'], (int, float))
    assert result['tags'] == ['A', 'B']


def test_save_current_without_tags(mock, watson, json_mock):
    watson.start('foo')

    mock.patch('%s.open' % builtins, mock.mock_open())
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert result['project'] == 'foo'
    assert isinstance(result['start'], (int, float))
    assert result['tags'] == []

    dump_args = json_mock.call_args[1]
    assert dump_args['ensure_ascii'] is False


def test_save_empty_current(config_dir, mock, json_mock):
    watson = Watson(current={}, config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open())

    watson.current = {'project': 'foo', 'start': 4000}
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert result == {'project': 'foo', 'start': 4000, 'tags': []}

    watson.current = {}
    watson.save()

    assert json_mock.call_count == 2
    result = json_mock.call_args[0][0]
    assert result == {}


def test_save_frames_no_change(config_dir, mock, json_mock):
    watson = Watson(frames=[[4000, 4010, 'foo', None]],
                    config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open())
    watson.save()

    assert not json_mock.called


def test_save_added_frame(config_dir, mock, json_mock):
    watson = Watson(frames=[[4000, 4010, 'foo', None]], config_dir=config_dir)
    watson.frames.add('bar', 4010, 4020, ['A'])

    mock.patch('%s.open' % builtins, mock.mock_open())
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert len(result) == 2
    assert result[0][2] == 'foo'
    assert result[0][4] == []
    assert result[1][2] == 'bar'
    assert result[1][4] == ['A']


def test_save_changed_frame(config_dir, mock, json_mock):
    watson = Watson(frames=[[4000, 4010, 'foo', None, ['A']]],
                    config_dir=config_dir)
    watson.frames[0] = ('bar', 4000, 4010, ['A', 'B'])

    mock.patch('%s.open' % builtins, mock.mock_open())
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert len(result) == 1
    assert result[0][2] == 'bar'
    assert result[0][4] == ['A', 'B']

    dump_args = json_mock.call_args[1]
    assert dump_args['ensure_ascii'] is False


def test_save_config_no_changes(mock, watson):
    mock.patch('%s.open' % builtins, mock.mock_open())
    write_mock = mock.patch.object(ConfigParser, 'write')
    watson.save()

    assert not write_mock.called


def test_save_config(mock, watson):
    mock.patch('%s.open' % builtins, mock.mock_open())
    write_mock = mock.patch.object(ConfigParser, 'write')
    watson.config = ConfigParser()
    watson.save()

    assert write_mock.call_count == 1


def test_save_last_sync(mock, watson, json_mock):
    now = arrow.now()
    watson.last_sync = now

    mock.patch('%s.open' % builtins, mock.mock_open())
    watson.save()

    assert json_mock.call_count == 1
    assert json_mock.call_args[0][0] == now.timestamp


def test_save_empty_last_sync(config_dir, mock, json_mock):
    watson = Watson(last_sync=arrow.now(), config_dir=config_dir)
    watson.last_sync = None

    mock.patch('%s.open' % builtins, mock.mock_open())
    watson.save()

    assert json_mock.call_count == 1
    assert json_mock.call_args[0][0] == 0


def test_watson_save_calls_safe_save(mock, config_dir, watson):
    frames_file = os.path.join(config_dir, 'frames')
    watson.start('foo', tags=['A', 'B'])
    watson.stop()

    save_mock = mock.patch('watson.watson.safe_save')
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


def test_push(mock, watson):
    config = ConfigParser()
    config.add_section('backend')
    config.set('backend', 'url', 'http://foo.com')
    config.set('backend', 'token', 'bar')

    watson.frames.add('foo', 4001, 4002)
    watson.frames.add('foo', 4003, 4004)

    watson.last_sync = arrow.now()

    watson.frames.add('bar', 4001, 4002, ['A', 'B'])
    watson.frames.add('lol', 4001, 4002)

    last_pull = arrow.now()

    watson.frames.add('foo', 4001, 4002)
    watson.frames.add('bar', 4003, 4004)

    mock.patch.object(watson, '_get_remote_projects', return_value=[
        {'name': 'foo', 'id': '08288b71-4500-40dd-96b1-a995937a15fd'},
        {'name': 'bar', 'id': 'f0534272-65fa-4832-a49e-0eedf68b3a84'},
        {'name': 'lol', 'id': '7fdaf65e-66bd-4c01-b09e-74bdc8cbe552'},
    ])

    class Response:
        def __init__(self):
            self.status_code = 201

    mock_put = mock.patch('requests.post', return_value=Response())
    mock.patch.object(Watson, 'config', new_callable=mock.PropertyMock,
                      return_value=config)
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

    assert frames_sent[0].get('project') == 'bar'
    assert frames_sent[0].get('tags') == ['A', 'B']

    assert frames_sent[1].get('project') == 'lol'
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


def test_pull(mock, watson):
    config = ConfigParser()
    config.add_section('backend')
    config.set('backend', 'url', 'http://foo.com')
    config.set('backend', 'token', 'bar')

    watson.last_sync = arrow.now()

    watson.frames.add(
        'foo', 4001, 4002, ['A', 'B'], id='1c006c6e6cc14c80ab22b51c857c0b06'
    )

    mock.patch.object(watson, '_get_remote_projects', return_value=[
        {'name': 'foo', 'id': '08288b71-4500-40dd-96b1-a995937a15fd'},
        {'name': 'bar', 'id': 'f0534272-65fa-4832-a49e-0eedf68b3a84'},
    ])

    class Response:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return [
                {
                    'id': '1c006c6e-6cc1-4c80-ab22-b51c857c0b06',
                    'project': 'foo',
                    'start_at': 4003,
                    'end_at': 4004,
                    'tags': ['A']
                },
                {
                    'id': 'c44aa815-4d77-4a58-bddd-1afa95562141',
                    'project': 'bar',
                    'start_at': 4004,
                    'end_at': 4005,
                    'tags': []
                }
            ]

    mock.patch('requests.get', return_value=Response())
    mock.patch.object(Watson, 'config', new_callable=mock.PropertyMock,
                      return_value=config)
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

    assert watson.frames[0].id == '1c006c6e6cc14c80ab22b51c857c0b06'
    assert watson.frames[0].project == 'foo'
    assert watson.frames[0].start.timestamp == 4003
    assert watson.frames[0].stop.timestamp == 4004
    assert watson.frames[0].tags == ['A']

    assert watson.frames[1].id == 'c44aa8154d774a58bddd1afa95562141'
    assert watson.frames[1].project == 'bar'
    assert watson.frames[1].start.timestamp == 4004
    assert watson.frames[1].stop.timestamp == 4005
    assert watson.frames[1].tags == []


# projects

def test_projects(watson):
    for name in ('foo', 'bar', 'bar', 'bar', 'foo', 'lol'):
        watson.frames.add(name, 4000, 4000)

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
        watson.frames.add(name, 4000, 4000, tags)

    assert watson.tags == ['A', 'B', 'C', 'D']


def test_tags_no_frames(watson):
    assert watson.tags == []


# merge

@pytest.mark.datafiles(
    TEST_FIXTURE_DIR / 'frames-with-conflict',
    )
def test_merge_report(watson, datafiles):
    # Get report
    watson.frames.add('foo', 4000, 4015, id='1', updated_at=4015)
    watson.frames.add('bar', 4020, 4045, id='2', updated_at=4045)

    conflicting, merging = watson.merge_report(
        str(datafiles) + '/frames-with-conflict')

    assert len(conflicting) == 1
    assert len(merging) == 1

    assert conflicting[0].id == '2'
    assert merging[0].id == '3'


def test_report(watson):
    watson.start('foo', tags=['A', 'B'])
    watson.stop()

    report = watson.report(arrow.now(), arrow.now())
    assert 'time' in report
    assert 'timespan' in report
    assert 'from' in report['timespan']
    assert 'to' in report['timespan']
    assert len(report['projects']) == 1
    assert report['projects'][0]['name'] == 'foo'
    assert len(report['projects'][0]['tags']) == 2
    assert report['projects'][0]['tags'][0]['name'] == 'A'
    assert 'time' in report['projects'][0]['tags'][0]
    assert report['projects'][0]['tags'][1]['name'] == 'B'
    assert 'time' in report['projects'][0]['tags'][1]

    watson.start('bar', tags=['C'])
    watson.stop()

    report = watson.report(arrow.now(), arrow.now())
    assert len(report['projects']) == 2
    assert report['projects'][0]['name'] == 'bar'
    assert report['projects'][1]['name'] == 'foo'
    assert len(report['projects'][0]['tags']) == 1
    assert report['projects'][0]['tags'][0]['name'] == 'C'

    report = watson.report(
        arrow.now(), arrow.now(), projects=['foo'], tags=['B']
    )
    assert len(report['projects']) == 1
    assert report['projects'][0]['name'] == 'foo'
    assert len(report['projects'][0]['tags']) == 1
    assert report['projects'][0]['tags'][0]['name'] == 'B'


# renaming project updates frame last_updated time
def test_rename_project_with_time(mock, watson):
    """
    Renaming a project should update the "last_updated" time on any frame that
    contains that project.
    """
    watson.frames.add(
        'foo', 4001, 4002, ['some_tag'],
        id='c76d1ad0282c429595cc566d7098c165', updated_at=4005
    )
    watson.frames.add(
        'bar', 4010, 4015, ['other_tag'],
        id='eed598ff363d42658a095ae6c3ae1088', updated_at=4035
    )

    watson.rename_project("foo", "baz")

    assert len(watson.frames) == 2

    assert watson.frames[0].id == 'c76d1ad0282c429595cc566d7098c165'
    assert watson.frames[0].project == 'baz'
    assert watson.frames[0].start.timestamp == 4001
    assert watson.frames[0].stop.timestamp == 4002
    assert watson.frames[0].tags == ['some_tag']
    # assert watson.frames[0].updated_at.timestamp == 9000
    assert watson.frames[0].updated_at.timestamp > 4005

    assert watson.frames[1].id == 'eed598ff363d42658a095ae6c3ae1088'
    assert watson.frames[1].project == 'bar'
    assert watson.frames[1].start.timestamp == 4010
    assert watson.frames[1].stop.timestamp == 4015
    assert watson.frames[1].tags == ['other_tag']
    assert watson.frames[1].updated_at.timestamp == 4035


def test_rename_tag_with_time(mock, watson):
    """
    Renaming a tag should update the "last_updated" time on any frame that
    contains that tag.
    """
    watson.frames.add(
        'foo', 4001, 4002, ['some_tag'],
        id='c76d1ad0282c429595cc566d7098c165', updated_at=4005
    )
    watson.frames.add(
        'bar', 4010, 4015, ['other_tag'],
        id='eed598ff363d42658a095ae6c3ae1088', updated_at=4035
    )

    watson.rename_tag("other_tag", "baz")

    assert len(watson.frames) == 2

    assert watson.frames[0].id == 'c76d1ad0282c429595cc566d7098c165'
    assert watson.frames[0].project == 'foo'
    assert watson.frames[0].start.timestamp == 4001
    assert watson.frames[0].stop.timestamp == 4002
    assert watson.frames[0].tags == ['some_tag']
    assert watson.frames[0].updated_at.timestamp == 4005

    assert watson.frames[1].id == 'eed598ff363d42658a095ae6c3ae1088'
    assert watson.frames[1].project == 'bar'
    assert watson.frames[1].start.timestamp == 4010
    assert watson.frames[1].stop.timestamp == 4015
    assert watson.frames[1].tags == ['baz']
    # assert watson.frames[1].updated_at.timestamp == 9000
    assert watson.frames[1].updated_at.timestamp > 4035

# add


def test_add_success(mock, watson):
    """
    Adding a new frame outside of live tracking successfully
    """
    watson.add(project="test_project", tags=['fuu', 'bar'],
               from_date=6000, to_date=7000)

    assert len(watson.frames) == 1
    assert watson.frames[0].project == "test_project"
    assert 'fuu' in watson.frames[0].tags


def test_add_failure(mock, watson):
    """
    Adding a new frame outside of live tracking fails when
    to date is before from date
    """
    with pytest.raises(WatsonError):
        watson.add(project="test_project", tags=['fuu', 'bar'],
                   from_date=7000, to_date=6000)
