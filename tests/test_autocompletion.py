"""Unit tests for the 'autocompletion' module."""

import json
import os
import py
import pytest

from watson import Watson


TEST_FIXTURE_DIR = py.path.local(
    os.path.dirname(
        os.path.realpath(__file__)
        )
    ) / 'resources'
AUTOCOMPLETION_FRAMES_PATH = TEST_FIXTURE_DIR / 'frames-with-conflict'
AUTOCOMPLETION_FRAMES = pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)


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
