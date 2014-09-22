import os
import json
import tempfile

import pytest
import click
import click.testing

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
