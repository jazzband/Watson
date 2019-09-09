"""Unit tests for the 'autocompletion' module."""

import json
import os
import pytest
import shutil

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


@AUTOCOMPLETION_FRAMES
def test_get_frames_returns_distinct(datafiles, monkeypatch):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = ''
    frame_id_list = list(get_frames(None, None, prefix))
    assert sorted(set(frame_id_list)) == sorted(frame_id_list)


@AUTOCOMPLETION_FRAMES
def test_complete_empty_frame_prefix(datafiles, monkeypatch):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = ''
    with open(str(AUTOCOMPLETION_FRAMES_PATH)) as fh:
        n_frames = len(json.load(fh))
    frame_ids = set(get_frames(None, None, prefix))
    assert len(frame_ids) == n_frames


@AUTOCOMPLETION_FRAMES
def test_not_existing_frame_prefix(datafiles, monkeypatch):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = 'NOT-EXISTING-PREFIX'
    frame_ids = set(get_frames(None, None, prefix))
    assert frame_ids == set()


@AUTOCOMPLETION_FRAMES
def test_existing_frame_prefix(datafiles, monkeypatch):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = 'f4f7'
    frame_ids = set(get_frames(None, None, prefix))
    assert len(frame_ids) == 2
    assert all(cur_frame_id.startswith(prefix) for cur_frame_id in frame_ids)
