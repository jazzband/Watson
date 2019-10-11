"""Unit tests for the 'autocompletion' module."""

import json
import os
import shutil

import pytest

from watson.autocompletion import (
    get_frames,
    get_project_or_task_completion,
    get_projects,
    get_rename_name,
    get_rename_types,
    get_tags,
)
from .conftest import TEST_FIXTURE_DIR


AUTOCOMPLETION_FRAMES_PATH = TEST_FIXTURE_DIR / "frames-for-autocompletion"
AUTOCOMPLETION_FRAMES = pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)
with open(str(AUTOCOMPLETION_FRAMES_PATH)) as fh:
    N_FRAMES = len(json.load(fh))
N_PROJECTS = 5
N_TASKS = 3
N_VARIATIONS_OF_PROJECT3 = 2
N_FRAME_IDS_FOR_PREFIX = 2


class CTXDummy:
    def __init__(self, rename_type):
        self.params = {"rename_type": rename_type}


@pytest.fixture
def prepare_sysenv_for_testing(datafiles, monkeypatch):
    shutil.copy(
        os.path.join(str(datafiles), "frames-for-autocompletion"),
        os.path.join(str(datafiles), "frames"),
    )
    monkeypatch.setenv("WATSON_DIR", str(datafiles))


@AUTOCOMPLETION_FRAMES
@pytest.mark.usefixtures("prepare_sysenv_for_testing")
@pytest.mark.parametrize(
    "func_to_test, ctx, args",
    [
        (get_frames, None, []),
        (get_project_or_task_completion, None, ["project1", "+tag1"]),
        (get_project_or_task_completion, None, []),
        (get_projects, None, []),
        (get_rename_name, CTXDummy("project"), []),
        (get_rename_name, CTXDummy("tag"), []),
        (get_rename_types, None, []),
        (get_tags, None, []),
    ],
)
def test_if_returned_values_are_distinct(func_to_test, ctx, args):
    prefix = ""
    ret_list = list(func_to_test(ctx, args, prefix))
    assert sorted(ret_list) == sorted(set(ret_list))


@AUTOCOMPLETION_FRAMES
@pytest.mark.usefixtures("prepare_sysenv_for_testing")
@pytest.mark.parametrize(
    "func_to_test, n_expected_returns, ctx, args",
    [
        (get_frames, N_FRAMES, None, []),
        (get_project_or_task_completion, N_TASKS, None, ["project1", "+"]),
        (get_project_or_task_completion, N_PROJECTS, None, []),
        (get_projects, N_PROJECTS, None, []),
        (get_rename_name, N_PROJECTS, CTXDummy("project"), []),
        (get_rename_name, N_TASKS, CTXDummy("tag"), []),
        (get_rename_types, 2, None, []),
        (get_tags, N_TASKS, None, []),
    ],
)
def test_if_empty_prefix_returns_everything(
    func_to_test, n_expected_returns, ctx, args
):
    prefix = ""
    completed_vals = set(func_to_test(ctx, args, prefix))
    assert len(completed_vals) == n_expected_returns


@AUTOCOMPLETION_FRAMES
@pytest.mark.usefixtures("prepare_sysenv_for_testing")
@pytest.mark.parametrize(
    "func_to_test, ctx, args",
    [
        (get_frames, None, []),
        (get_project_or_task_completion, None, ["project1", "+"]),
        (get_project_or_task_completion, None, ["project1", "+tag1", "+"]),
        (get_project_or_task_completion, None, []),
        (get_projects, None, []),
        (get_rename_name, CTXDummy("project"), []),
        (get_rename_name, CTXDummy("tag"), []),
        (get_rename_types, None, []),
        (get_tags, None, []),
    ],
)
def test_completion_of_nonexisting_prefix(func_to_test, ctx, args):
    prefix = "NOT-EXISTING-PREFIX"
    ret_list = list(func_to_test(ctx, args, prefix))
    assert not ret_list


@AUTOCOMPLETION_FRAMES
@pytest.mark.usefixtures("prepare_sysenv_for_testing")
@pytest.mark.parametrize(
    "func_to_test, prefix, n_expected_vals, ctx, args",
    [
        (get_frames, "f4f7", N_FRAME_IDS_FOR_PREFIX, None, []),
        (
            get_project_or_task_completion,
            "+tag",
            N_TASKS,
            None,
            ["project1", "+tag3"],
        ),
        (get_project_or_task_completion, "+tag", N_TASKS, None, ["project1"]),
        (
            get_project_or_task_completion,
            "project3",
            N_VARIATIONS_OF_PROJECT3,
            None,
            [],
        ),
        (get_projects, "project3", N_VARIATIONS_OF_PROJECT3, None, []),
        (
            get_rename_name,
            "project3",
            N_VARIATIONS_OF_PROJECT3,
            CTXDummy("project"),
            [],
        ),
        (get_rename_name, "tag", N_TASKS, CTXDummy("tag"), []),
        (get_rename_types, "ta", 1, None, []),
        (get_tags, "tag", N_TASKS, None, []),
    ],
)
def test_completion_of_existing_prefix(
    func_to_test, prefix, n_expected_vals, ctx, args
):
    ret_set = set(func_to_test(ctx, args, prefix))
    assert len(ret_set) == n_expected_vals
    assert all(cur_elem.startswith(prefix) for cur_elem in ret_set)


@AUTOCOMPLETION_FRAMES
@pytest.mark.usefixtures("prepare_sysenv_for_testing")
@pytest.mark.parametrize(
    "func_to_test, prefix, expected_vals",
    [
        (get_rename_types, "", ["project", "tag"]),
        (get_rename_types, "t", ["tag"]),
        (get_rename_types, "p", ["project"]),
    ],
)
def test_for_known_completion_values(func_to_test, prefix, expected_vals):
    ret_list = list(func_to_test(None, [], prefix))
    assert ret_list == expected_vals
