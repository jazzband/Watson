import os
import json
import tempfile

import pytest
import mock
import click
import click.testing
import requests

import watson


@pytest.fixture
def watson_file(request):
    fd, name = tempfile.mkstemp()
    os.fdopen(fd).close()
    watson.WATSON_FILE = name

    def clean():
        try:
            os.unlink(name)
        except IOError:
            pass

    request.addfinalizer(clean)

    return name


@pytest.fixture
def watson_conf(request):
    fd, name = tempfile.mkstemp()
    os.fdopen(fd).close()
    watson.WATSON_CONF = name

    try:
        from ConfigParser import SafeConfigParser
    except ImportError:
        from configparser import SafeConfigParser

    config = SafeConfigParser()
    config['crick'] = {
        'url': 'http://localhost:8000/api',
        'token': '7e329263e329646be79d6cc3b3af7bf48b6b1779'
    }

    with open(name, 'w+') as f:
        config.write(f)

    def clean():
        try:
            os.unlink(name)
        except IOError:
            pass

    request.addfinalizer(clean)

    return config


@pytest.fixture
def runner():
    return click.testing.CliRunner()


# get_watson

def test_get_watson(watson_file):
    content = {'foo': 'bar'}

    with open(watson_file, 'w+') as f:
        json.dump(content, f)

    assert watson.get_watson() == content


def test_get_watson_empty_file(watson_file):
    assert watson.get_watson() == {}


def test_get_watson_nonexistent_file(watson_file):
    os.unlink(watson_file)
    assert watson.get_watson() == {}


def test_get_watson_non_valid_json(watson_file):
    content = "{'foo': bar}"

    with open(watson_file, 'w+') as f:
        f.write(content)

    with pytest.raises(click.ClickException):
        watson.get_watson()


# save_watson

def test_save_watson(watson_file):
    content = {'test': 1234}

    watson.save_watson(content)

    with open(watson_file) as f:
        assert json.load(f) == content


def test_save_watson_nonexistent_file(watson_file):
    content = {'Obi-Wan': 'Kenobi'}

    # We delete the tmp file and let save_watson
    # create it again. This is a race-condition,
    # as another process could have created
    # a file with the same name in the
    # meantime. However it is very unlikely.
    os.unlink(watson_file)
    watson.save_watson(content)

    with open(watson_file) as f:
        assert json.load(f) == content


# start

def test_start_new_project(watson_file, runner):
    r = runner.invoke(watson.start, ('test',))
    assert r.exit_code == 0

    with open(watson_file) as f:
        content = json.load(f)

    assert 'current' in content
    assert content['current'].get('project') == ['test']
    assert 'start' in content['current']


def test_start_new_subprojects(watson_file, runner):
    r = runner.invoke(watson.start, ('foo', 'bar', 'lol'))
    assert r.exit_code == 0

    with open(watson_file) as f:
        content = json.load(f)

    assert 'current' in content
    assert content['current'].get('project') == ['foo', 'bar', 'lol']


def test_start_new_subprojects_with_slash(watson_file, runner):
    r = runner.invoke(watson.start, ('foo/bar', 'lol', 'x/y'))
    assert r.exit_code == 0

    with open(watson_file) as f:
        content = json.load(f)

    assert 'current' in content
    assert content['current'].get('project') == ['foo', 'bar', 'lol', 'x', 'y']


def test_start_two_projects(watson_file, runner):
    r = runner.invoke(watson.start, ('foo',))
    assert r.exit_code == 0

    r = runner.invoke(watson.start, ('bar',))
    assert r.exit_code != 0


# stop

def test_stop_started_project(watson_file, runner):
    r = runner.invoke(watson.start, ('foo',))
    assert r.exit_code == 0

    r = runner.invoke(watson.stop)
    assert r.exit_code == 0

    with open(watson_file) as f:
        content = json.load(f)

    assert 'current' not in content
    assert 'projects' in content
    assert 'foo' in content['projects']
    frames = content['projects']['foo'].get('frames')
    assert len(frames) == 1
    assert 'start' in frames[0]
    assert 'stop' in frames[0]


def test_stop_started_subproject(watson_file, runner):
    r = runner.invoke(watson.start, ('foo', 'bar', 'lol'))
    assert r.exit_code == 0

    r = runner.invoke(watson.stop)
    assert r.exit_code == 0

    with open(watson_file) as f:
        content = json.load(f)

    assert 'current' not in content
    assert 'projects' in content
    foo = content['projects'].get('foo')
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


def test_stop_no_project(watson_file, runner):
    r = runner.invoke(watson.stop)
    assert r.exit_code != 0


# cancel

def test_cancel_started_project(watson_file, runner):
    r = runner.invoke(watson.start, ('foo',))
    assert r.exit_code == 0

    r = runner.invoke(watson.stop)
    assert r.exit_code == 0

    with open(watson_file) as f:
        content = json.load(f)

    assert 'current' not in content


def test_cancel_no_project(watson_file, runner):
    r = runner.invoke(watson.stop)
    assert r.exit_code != 0


# status

def test_status_project_started(runner):
    r = runner.invoke(watson.start, ('foo',))
    assert r.exit_code == 0

    r = runner.invoke(watson.status)
    assert r.exit_code == 0


def test_status_no_project(runner):
    r = runner.invoke(watson.status)
    assert r.exit_code == 0


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


def test_push(watson_conf, watson_file, project_tree, runner):
    with open(watson_file, 'w') as f:
        json.dump(project_tree, f)

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

        r = runner.invoke(watson.push)
        assert r.exit_code == 0

        requests.post.assert_called_once_with(
            watson_conf['crick']['url'] + '/frames/',
            mock.ANY,
            headers={
                'content-type': 'application/json',
                'Authorization': "Token " + watson_conf['crick']['token']
            }
        )

        frames_received = json.loads(mock_post.call_args[0][1])['frames']
        assert frames_received == frames

    with open(watson_file) as f:
        p = json.load(f).get('projects')
        assert p

    assert p["A"]['projects']["X"]['projects']["foo"]['frames'][0]['id'] == 0
    assert p["A"]['projects']["X"]['frames'][0]['id'] == 1
    assert p["A"]['projects']["Y"]['projects']["toto"]['frames'][0]['id'] == 2
    assert p["A"]['projects']["Y"]['projects']["toto"]['frames'][1]['id'] == 3
    assert p["A"]['projects']["Y"]['frames'][0]['id'] == 4
    assert p["A"]['frames'][0]['id'] == 5
    assert p["B"]['frames'][1]['id'] == 6


def test_push_force(watson_conf, watson_file, project_tree, runner):
    with open(watson_file, 'w') as f:
        json.dump(project_tree, f)

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

            r = runner.invoke(watson.push, ('-f',))
            assert r.exit_code == 0

            args = (watson_conf['crick']['url'] + '/frames/', mock.ANY)
            kwargs = {
                'headers': {
                    'content-type': 'application/json',
                    'Authorization': "Token " + watson_conf['crick']['token']
                }
            }
            requests.post.assert_called_once_with(*args, **kwargs)
            requests.put.assert_called_once_with(*args, **kwargs)

            frames_received = json.loads(mock_put.call_args[0][1])['frames']
            sort = lambda f: sorted(f, key=lambda e: e['id'])
            assert sort(frames_received) == sort(frames)
