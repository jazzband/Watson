"""Unit tests for the 'autocompletion' module."""

import json
import os
import pytest
import shutil

from watson.autocompletion import (
    get_frames,
    get_projects,
    get_rename_types,
)
from .conftest import TEST_FIXTURE_DIR


AUTOCOMPLETION_FRAMES_PATH = TEST_FIXTURE_DIR / 'frames-for-autocompletion'
AUTOCOMPLETION_FRAMES = pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)
with open(str(AUTOCOMPLETION_FRAMES_PATH)) as fh:
    N_FRAMES = len(json.load(fh))


def prepare_sysenv_for_testing(config_dirname, monkeypatch):
    shutil.copy(
        os.path.join(str(config_dirname), "frames-for-autocompletion"),
        os.path.join(str(config_dirname), "frames"),
        )
    monkeypatch.setenv('WATSON_DIR', str(config_dirname))


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test', [
    get_frames,
    get_projects,
    get_rename_types,
])
def test_if_returned_values_are_distinct(datafiles, monkeypatch, func_to_test):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = ''
    ret_list = list(func_to_test(None, None, prefix))
    assert sorted(ret_list) == sorted(set(ret_list))


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test, n_expected_returns', [
    (get_frames, N_FRAMES),
    (get_projects, 5),
    (get_rename_types, 2),
])
def test_if_empty_prefix_returns_everything(
    datafiles,
    monkeypatch,
    func_to_test,
    n_expected_returns,
):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = ''
    completed_vals = set(func_to_test(None, None, prefix))
    assert len(completed_vals) == n_expected_returns


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test', [
    get_frames,
    get_projects,
    get_rename_types,
])
def test_completion_of_nonexisting_prefix(
    datafiles,
    monkeypatch,
    func_to_test
):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = 'NOT-EXISTING-PREFIX'
    ret_list = list(func_to_test(None, None, prefix))
    assert not ret_list


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test, prefix, n_expected_vals', [
    (get_frames, 'f4f7', 2),
    (get_projects, 'project3', 2),
    (get_rename_types, 'ta', 1),
])
def test_completion_of_existing_prefix(
    datafiles,
    monkeypatch,
    func_to_test,
    prefix,
    n_expected_vals,
):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    ret_set = set(func_to_test(None, None, prefix))
    assert len(ret_set) == n_expected_vals
    assert all(cur_elem.startswith(prefix) for cur_elem in ret_set)


@AUTOCOMPLETION_FRAMES
    prepare_sysenv_for_testing(datafiles, monkeypatch)
