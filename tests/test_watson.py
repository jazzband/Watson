import json

from unittest import mock

import pytest
import requests

from watson import Watson, WatsonError
from watson.watson import ConfigParser


@pytest.fixture
def watson():
    return Watson({})


# init

def test_init():
    content = json.dumps(
        {'projects': {'foo': {}}, 'current': {'project': 'foo'}}
    )

    with mock.patch('builtins.open', mock.mock_open(read_data=content)):
        watson = Watson()

    assert watson.tree
    assert 'projects' in watson.tree
    assert 'foo' in watson.tree['projects']
    assert watson.current
    assert watson.current['project'] == 'foo'
    assert watson.current['start']


def test_init_with_empty_file():
    with mock.patch('builtins.open', mock.mock_open(read_data="")):
        with mock.patch('os.path.getsize', return_value=0):
            watson = Watson()

    assert watson.tree
    assert 'projects' in watson.tree
    assert watson.tree['projects'] == {}
    assert not watson.current


def test_init_with_nonexistent_file():
    with mock.patch('builtins.open', side_effect=IOError):
        watson = Watson()

    assert watson.tree
    assert 'projects' in watson.tree
    assert watson.tree['projects'] == {}
    assert not watson.current


def test_init_watson_non_valid_json():
    content = "{'foo': bar}"

    with mock.patch('builtins.open', mock.mock_open(read_data=content)):
        with pytest.raises(WatsonError):
            Watson()


def test_init_with_content():
    content = json.dumps(
        {'projects': {'foo': {}}, 'current': {'project': 'foo'}}
    )

    with mock.patch('builtins.open', mock.mock_open(read_data=content)):
        watson = Watson({'projects': {'bar': {}}})

    assert watson.current is None
    assert 'bar' in watson.tree['projects']
    assert 'foo' not in watson.tree['projects']


def test_init_with_empty_content():
    content = json.dumps(
        {'projects': {'foo': {}}, 'current': {'project': 'foo'}}
    )

    with mock.patch('builtins.open', mock.mock_open(read_data=content)):
        watson = Watson({})

    assert watson.current is None
    assert not watson.tree['projects']


# config

def test_config(watson):
    content = """
[crick]
url = foo
token = bar
    """
    mocked_read = lambda self, name: self.read_string(content)
    with mock.patch.object(ConfigParser, 'read', mocked_read):
        config = watson.config
        assert 'crick' in config
        assert config['crick'] == {'url': 'foo', 'token': 'bar'}


def test_config_without_url(watson):
    content = """
[crick]
token = bar
    """
    mocked_read = lambda self, name: self.read_string(content)
    with mock.patch.object(ConfigParser, 'read', mocked_read):
        with pytest.raises(WatsonError):
            watson.config


def test_config_without_token(watson):
    content = """
[crick]
token = bar
    """
    mocked_read = lambda self, name: self.read_string(content)
    with mock.patch.object(ConfigParser, 'read', mocked_read):
        with pytest.raises(WatsonError):
            watson.config


def test_no_config(watson):
    with mock.patch('builtins.open', side_effect=IOError):
        with pytest.raises(WatsonError):
            watson.config


# dump

def test_dump_when_not_started():
    content = {'projects': {'foo': {}}}
    watson = Watson(content)
    dump = watson.dump()

    assert id(dump) != id(content)
    assert dump == content


def test_dump_when_started():
    content = {'projects': {'foo': {}}, 'current': {'project': 'foo'}}
    watson = Watson(content)
    dump = watson.dump()

    assert id(dump) != id(content)
    assert 'projects' in dump
    assert dump['projects'] == content['projects']
    assert 'current' in dump
    assert 'project' in dump['current']
    assert dump['current']['project'] == 'foo'
    assert 'start' in dump['current']


# start

def test_start_new_project(watson):
    watson.start('foo')

    assert watson.current
    assert watson.is_started is True
    assert watson.current.get('project') == 'foo'
    assert watson.current.get('start')


def test_start_new_subprojects(watson):
    watson.start('foo/bar/lol')

    assert watson.current
    assert watson.is_started is True
    assert watson.current.get('project') == 'foo/bar/lol'


def test_start_two_projects(watson):
    watson.start('foo')

    with pytest.raises(WatsonError):
        watson.start('bar')

    assert watson.current
    assert watson.current['project'] == 'foo'
    assert watson.is_started is True


# stop

def test_stop_started_project(watson):
    watson.start('foo')
    watson.stop('foo')

    assert watson.current is None
    assert watson.is_started is False
    assert 'foo' in watson.tree.get('projects')
    frames = watson.tree['projects']['foo'].get('frames')
    assert len(frames) == 1
    assert 'start' in frames[0]
    assert 'stop' in frames[0]


def test_stop_started_subproject(watson):
    watson.start('foo/bar/lol')
    watson.stop()

    assert watson.current is None
    assert watson.is_started is False
    foo = watson.tree['projects'].get('foo')
    assert foo
    assert foo.get('frames') == []
    bar = foo['projects'].get('bar')
    assert bar
    assert bar.get('frames') == []
    lol = bar['projects'].get('lol')
    assert lol
    assert len(lol['frames']) == 1
    assert 'start' in lol['frames'][0]
    assert 'stop' in lol['frames'][0]


def test_stop_no_project(watson):
    with pytest.raises(WatsonError):
        watson.stop()


# cancel

def test_cancel_started_project(watson):
    watson.start('foo')
    watson.cancel()

    assert watson.current is None
    assert 'foo' not in watson.tree['projects']


def test_cancel_no_project(watson):
    with pytest.raises(WatsonError):
        watson.cancel()


# push

@pytest.fixture
def project_tree():
    return {
        "projects": {
            "A": {
                "projects": {
                    "X": {
                        "projects": {
                            "foo": {
                                "projects": {},
                                "frames": [
                                    {"start": "01", "stop": "01"},
                                ]
                            }
                        },
                        "frames": [
                            {"start": "02", "stop": "02"},
                            {"start": "03", "stop": "03", "id": 42},


                        ]
                    },
                    "Y": {
                        "projects": {
                            "toto": {
                                "projects": {},
                                "frames": [
                                    {"start": "04", "stop": "04"},
                                    {"start": "05", "stop": "05"},
                                ]
                            }
                        },
                        "frames": [
                            {"start": "06", "stop": "06"},
                        ]
                    }
                },
                "frames": [
                    {"start": "07", "stop": "07"},
                ]
            },
            "B": {
                "projects": {},
                "frames": [
                    {"start": "08", "stop": "08", "id": 24},
                    {"start": "09", "stop": "09"}
                ]
            }
        }
    }


def test_push(project_tree):
    watson = Watson(project_tree)

    config = {'crick': {'url': 'http://foo.com', 'token': 'toto'}}

    frames = [
        {"start": "01", "stop": "01", "project": ["A", "X", "foo"]},
        {"start": "02", "stop": "02", "project": ["A", "X"]},
        {"start": "04", "stop": "04", "project": ["A", "Y", "toto"]},
        {"start": "05", "stop": "05", "project": ["A", "Y", "toto"]},
        {"start": "06", "stop": "06", "project": ["A", "Y"]},
        {"start": "07", "stop": "07", "project": ["A"]},
        {"start": "09", "stop": "09", "project": ["B"]},
    ]

    class Response:
        def __init__(self):
            self.status_code = 201

        def json(self):
            return list(range(len(frames)))

    with mock.patch('requests.post') as mock_post:
        mock_post.return_value = Response()

        with mock.patch.object(
                Watson, 'config', new_callable=mock.PropertyMock
                ) as mock_config:
            mock_config.return_value = config
            watson.push()

        requests.post.assert_called_once_with(
            config['crick']['url'] + '/frames/',
            mock.ANY,
            headers={
                'content-type': 'application/json',
                'Authorization': "Token " + config['crick']['token']
            }
        )

        frames_received = json.loads(mock_post.call_args[0][1])['frames']
        assert frames_received == frames

    p = watson.tree['projects']

    assert p["A"]['projects']["X"]['projects']["foo"]['frames'][0]['id'] == 0
    assert p["A"]['projects']["X"]['frames'][0]['id'] == 1
    assert p["A"]['projects']["Y"]['projects']["toto"]['frames'][0]['id'] == 2
    assert p["A"]['projects']["Y"]['projects']["toto"]['frames'][1]['id'] == 3
    assert p["A"]['projects']["Y"]['frames'][0]['id'] == 4
    assert p["A"]['frames'][0]['id'] == 5
    assert p["B"]['frames'][1]['id'] == 6


def test_push_force(project_tree):
    watson = Watson(project_tree)

    config = {'crick': {'url': 'http://foo.com/', 'token': 'toto'}}

    frames = [
        {"start": "03", "stop": "03", "project": ["A", "X"], "id": 42},
        {"start": "08", "stop": "08", "project": ["B"], "id": 24},
    ]

    class PutResponse:
        def __init__(self):
            self.status_code = 200

    class PostResponse:
        def __init__(self):
            self.status_code = 201

        def json(self):
            return list(range(len(frames)))

    with mock.patch('requests.put') as mock_put:
        with mock.patch('requests.post') as mock_post:
            mock_put.return_value = PutResponse()
            mock_post.return_value = PostResponse()

            with mock.patch.object(
                    Watson, 'config', new_callable=mock.PropertyMock
                    ) as mock_config:
                mock_config.return_value = config
                watson.push(force=True)

            args = (config['crick']['url'] + '/frames/', mock.ANY)
            kwargs = {
                'headers': {
                    'content-type': 'application/json',
                    'Authorization': "Token " + config['crick']['token']
                }
            }
            requests.post.assert_called_once_with(*args, **kwargs)
            requests.put.assert_called_once_with(*args, **kwargs)

            frames_received = json.loads(mock_put.call_args[0][1])['frames']
            sort = lambda f: sorted(f, key=lambda e: e['id'])
            assert sort(frames_received) == sort(frames)


# projects

def test_projects(project_tree):
    watson = Watson(project_tree)

    assert watson.projects() == [
        'A',
        'A/X',
        'A/X/foo',
        'A/Y',
        'A/Y/toto',
        'B'
    ]


def test_projects_empty(watson, project_tree):
    assert watson.projects() == []
