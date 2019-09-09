"""Unit tests for the 'autocompletion' module."""

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
def test_get_frames(datafiles, monkeypatch):
    prepare_sysenv_for_testing(datafiles, monkeypatch)

    all_frames = set(get_frames(None, None, ''))
    assert len(all_frames) == 10
