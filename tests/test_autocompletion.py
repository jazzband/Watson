"""Unit tests for the 'autocompletion' module."""

import json
import os
import pytest
import shutil

from watson.autocompletion import (
    get_frames,
    get_projects,
    get_rename_name,
    get_rename_types,
    get_tags,
)
from .conftest import TEST_FIXTURE_DIR


AUTOCOMPLETION_FRAMES_PATH = TEST_FIXTURE_DIR / 'frames-for-autocompletion'
AUTOCOMPLETION_FRAMES = pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)
with open(str(AUTOCOMPLETION_FRAMES_PATH)) as fh:
    N_FRAMES = len(json.load(fh))


class CTXDummy():
    def __init__(self, rename_type):
        self.params = {"rename_type": rename_type}


def prepare_sysenv_for_testing(config_dirname, monkeypatch):
    shutil.copy(
        os.path.join(str(config_dirname), "frames-for-autocompletion"),
        os.path.join(str(config_dirname), "frames"),
        )
    monkeypatch.setenv('WATSON_DIR', str(config_dirname))


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test, ctx', [
    (get_frames, None),
    (get_projects, None),
    (get_rename_name, CTXDummy("project")),
    (get_rename_name, CTXDummy("tag")),
    (get_rename_types, None),
    (get_tags, None),
])
def test_if_returned_values_are_distinct(
    datafiles,
    monkeypatch,
    func_to_test,
    ctx,
):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = ''
    ret_list = list(func_to_test(ctx, None, prefix))
    assert sorted(ret_list) == sorted(set(ret_list))


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test, n_expected_returns, ctx', [
    (get_frames, N_FRAMES, None),
    (get_projects, 5, None),
    (get_rename_name, 5, CTXDummy("project")),
    (get_rename_name, 3, CTXDummy("tag")),
    (get_rename_types, 2, None),
    (get_tags, 3, None),
])
def test_if_empty_prefix_returns_everything(
    datafiles,
    monkeypatch,
    func_to_test,
    n_expected_returns,
    ctx,
):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = ''
    completed_vals = set(func_to_test(ctx, None, prefix))
    assert len(completed_vals) == n_expected_returns


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test, ctx', [
    (get_frames, None),
    (get_projects, None),
    (get_rename_name, CTXDummy("project")),
    (get_rename_name, CTXDummy("tag")),
    (get_rename_types, None),
    (get_tags, None),
])
def test_completion_of_nonexisting_prefix(
    datafiles,
    monkeypatch,
    func_to_test,
    ctx,
):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    prefix = 'NOT-EXISTING-PREFIX'
    ret_list = list(func_to_test(ctx, None, prefix))
    assert not ret_list


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test, prefix, n_expected_vals, ctx', [
    (get_frames, 'f4f7', 2, None),
    (get_projects, 'project3', 2, None),
    (get_rename_name, 'project3', 2, CTXDummy("project")),
    (get_rename_name, 'tag', 3, CTXDummy("tag")),
    (get_rename_types, 'ta', 1, None),
    (get_tags, 'tag', 3, None),
])
def test_completion_of_existing_prefix(
    datafiles,
    monkeypatch,
    func_to_test,
    prefix,
    n_expected_vals,
    ctx,
):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    ret_set = set(func_to_test(ctx, None, prefix))
    assert len(ret_set) == n_expected_vals
    assert all(cur_elem.startswith(prefix) for cur_elem in ret_set)


@AUTOCOMPLETION_FRAMES
@pytest.mark.parametrize('func_to_test, prefix, expected_vals', [
    (get_rename_types, "", ["project", "tag"]),
    (get_rename_types, "t", ["tag"]),
    (get_rename_types, "p", ["project"]),
])
def test_for_known_completion_values(
    datafiles,
    monkeypatch,
    func_to_test,
    prefix,
    expected_vals
):
    prepare_sysenv_for_testing(datafiles, monkeypatch)
    ret_list = list(func_to_test(None, None, prefix))
    assert ret_list == expected_vals
