"""Unit tests for the 'autocompletion' module."""

import json
import os
import pytest
import shutil

from watson import Watson
from watson.autocompletion import (
    get_frames,
)
from .conftest import TEST_FIXTURE_DIR


AUTOCOMPLETION_FRAMES_PATH = TEST_FIXTURE_DIR / 'frames-for-autocompletion'
AUTOCOMPLETION_FRAMES = pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)


def prepare_sysenv_for_testing(config_dirname, monkeypatch):
    shutil.copy(
        os.path.join(str(config_dirname), "frames-for-autocompletion"),
        os.path.join(str(config_dirname), "frames"),
        )
    monkeypatch.setenv('WATSON_DIR', str(config_dirname))


@pytest.fixture
def frames_file():
    return str(AUTOCOMPLETION_FRAMES_PATH)


@pytest.fixture
def watson(config_dir, frames_file):
    in_frames_file = frames_file
    with open(in_frames_file) as in_frames_fh:
        list_of_frames = json.load(in_frames_fh)
    return Watson(config_dir=config_dir, frames=list_of_frames)


@AUTOCOMPLETION_FRAMES
def test_watson(watson):
    projects = set(cur_frame[2] for cur_frame in watson.frames.dump())
    assert projects == set(('foo', 'bar'))


@AUTOCOMPLETION_FRAMES
def test_get_frames(datafiles, monkeypatch):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    frames = set(get_frames(None, None, ''))
    assert {"1", "2", "3"} == frames
