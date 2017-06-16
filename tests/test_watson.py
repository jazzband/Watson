"""Unit tests for the main 'watson' module."""

import json
import os
import sys

import py
import pytest
import requests
import arrow

from click import get_app_dir
from watson import Watson, WatsonError
from watson.watson import ConfigurationError, ConfigParser

from . import mock_read


PY2 = sys.version_info[0] == 2
TEST_FIXTURE_DIR = py.path.local(
    os.path.dirname(
        os.path.realpath(__file__)
        )
    ) / 'resources'

if not PY2:
    builtins = 'builtins'
else:
    builtins = '__builtin__'


# current

def test_current(mock, watson):
    content = json.dumps({'project': 'foo', 'start': 0, 'tags': ['A', 'B']})

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.current['project'] == 'foo'
    assert watson.current['start'] == arrow.get(0)
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
    content = json.dumps({'project': 'foo', 'start': 0})
    watson = Watson(current={'project': 'bar', 'start': 0},
                    config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.current['project'] == 'bar'


def test_current_with_empty_given_state(config_dir, mock):
    content = json.dumps({'project': 'foo', 'start': 0})
    watson = Watson(current=[], config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert watson.current == {}


# last_sync

def test_last_sync(mock, watson):
    now = arrow.get(123)
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
    content = json.dumps([[0, 10, 'foo', None, ['A', 'B', 'C']]])

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert len(watson.frames) == 1
    assert watson.frames[0].project == 'foo'
    assert watson.frames[0].start == arrow.get(0)
    assert watson.frames[0].stop == arrow.get(10)
    assert watson.frames[0].tags == ['A', 'B', 'C']


def test_frames_without_tags(mock, watson):
    content = json.dumps([[0, 10, 'foo', None]])

    mock.patch('%s.open' % builtins, mock.mock_open(read_data=content))
    assert len(watson.frames) == 1
    assert watson.frames[0].project == 'foo'
    assert watson.frames[0].start == arrow.get(0)
    assert watson.frames[0].stop == arrow.get(10)
    assert watson.frames[0].tags == []


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
    content = json.dumps([[0, 10, 'foo', None, ['A']]])
    watson = Watson(frames=[[0, 10, 'bar', None, ['A', 'B']]],
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

def test_save_without_changes(mock, watson):
    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
    watson.save()

    assert not json_mock.called


def test_save_current(mock, watson):
    watson.start('foo', ['A', 'B'])

    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert result['project'] == 'foo'
    assert isinstance(result['start'], (int, float))
    assert result['tags'] == ['A', 'B']


def test_save_current_without_tags(mock, watson):
    watson.start('foo')

    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert result['project'] == 'foo'
    assert isinstance(result['start'], (int, float))
    assert result['tags'] == []

    dump_args = json_mock.call_args[1]
    assert dump_args['ensure_ascii'] is False


def test_save_empty_current(config_dir, mock):
    watson = Watson(current={'project': 'foo', 'start': 0},
                    config_dir=config_dir)
    watson.current = {}

    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert result == {}


def test_save_frames_no_change(config_dir, mock):
    watson = Watson(frames=[[0, 10, 'foo', None]],
                    config_dir=config_dir)

    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
    watson.save()

    assert not json_mock.called


def test_save_added_frame(config_dir, mock):
    watson = Watson(frames=[[0, 10, 'foo', None]], config_dir=config_dir)
    watson.frames.add('bar', 10, 20, ['A'])

    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
    watson.save()

    assert json_mock.call_count == 1
    result = json_mock.call_args[0][0]
    assert len(result) == 2
    assert result[0][2] == 'foo'
    assert result[0][4] == []
    assert result[1][2] == 'bar'
    assert result[1][4] == ['A']


def test_save_changed_frame(config_dir, mock):
    watson = Watson(frames=[[0, 10, 'foo', None, ['A']]],
                    config_dir=config_dir)
    watson.frames[0] = ('bar', 0, 10, ['A', 'B'])

    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
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


def test_save_last_sync(mock, watson):
    now = arrow.now()
    watson.last_sync = now

    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
    watson.save()

    assert json_mock.call_count == 1
    assert json_mock.call_args[0][0] == now.timestamp


def test_save_empty_last_sync(config_dir, mock):
    watson = Watson(last_sync=arrow.now(), config_dir=config_dir)
    watson.last_sync = None

    mock.patch('%s.open' % builtins, mock.mock_open())
    json_mock = mock.patch('json.dump')
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

    watson.frames.add('foo', 1, 2)
    watson.frames.add('foo', 3, 4)

    watson.last_sync = arrow.now()

    watson.frames.add('bar', 1, 2, ['A', 'B'])
    watson.frames.add('lol', 1, 2)

    last_pull = arrow.now()

    watson.frames.add('foo', 1, 2)
    watson.frames.add('bar', 3, 4)

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
        'foo', 1, 2, ['A', 'B'], id='1c006c6e6cc14c80ab22b51c857c0b06'
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
                    'start_at': 3,
                    'end_at': 4,
                    'tags': ['A']
                },
                {
                    'id': 'c44aa815-4d77-4a58-bddd-1afa95562141',
                    'project': 'bar',
                    'start_at': 4,
                    'end_at': 5,
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
    assert watson.frames[0].start.timestamp == 3
    assert watson.frames[0].stop.timestamp == 4
    assert watson.frames[0].tags == ['A']

    assert watson.frames[1].id == 'c44aa8154d774a58bddd1afa95562141'
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
