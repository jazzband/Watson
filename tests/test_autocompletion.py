"""Unit tests for the 'autocompletion' module."""

import json
from argparse import Namespace

import pytest

from watson.autocompletion import (
    get_frames,
    get_project_or_task_completion,
    get_projects,
    get_rename_name,
    get_rename_types,
    get_tags,
)

from . import TEST_FIXTURE_DIR


AUTOCOMPLETION_FRAMES_PATH = TEST_FIXTURE_DIR / "autocompletion"
with open(str(AUTOCOMPLETION_FRAMES_PATH / "frames")) as fh:
    N_FRAMES = len(json.load(fh))
N_PROJECTS = 5
N_TASKS = 3
N_VARIATIONS_OF_PROJECT3 = 2
N_FRAME_IDS_FOR_PREFIX = 2

ClickContext = Namespace


@pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)
@pytest.mark.parametrize(
    "func_to_test, rename_type, args",
    [
        (get_frames, None, []),
        (get_project_or_task_completion, None, ["project1", "+tag1"]),
        (get_project_or_task_completion, None, []),
        (get_projects, None, []),
        (get_rename_name, "project", []),
        (get_rename_name, "tag", []),
        (get_rename_types, None, []),
        (get_tags, None, []),
    ],
)
def test_if_returned_values_are_distinct(
    watson_df, func_to_test, rename_type, args
):
    ctx = ClickContext(obj=watson_df, params={"rename_type": rename_type})
    prefix = ""
    ret_list = list(func_to_test(ctx, args, prefix))
    assert sorted(ret_list) == sorted(set(ret_list))


@pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)
@pytest.mark.parametrize(
    "func_to_test, n_expected_returns, rename_type, args",
    [
        (get_frames, N_FRAMES, None, []),
        (get_project_or_task_completion, N_TASKS, None, ["project1", "+"]),
        (get_project_or_task_completion, N_PROJECTS, None, []),
        (get_projects, N_PROJECTS, None, []),
        (get_rename_name, N_PROJECTS, "project", []),
        (get_rename_name, N_TASKS, "tag", []),
        (get_rename_types, 2, None, []),
        (get_tags, N_TASKS, None, []),
    ],
)
def test_if_empty_prefix_returns_everything(
    watson_df, func_to_test, n_expected_returns, rename_type, args
):
    prefix = ""
    ctx = ClickContext(obj=watson_df, params={"rename_type": rename_type})
    completed_vals = set(func_to_test(ctx, args, prefix))
    assert len(completed_vals) == n_expected_returns


@pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)
@pytest.mark.parametrize(
    "func_to_test, rename_type, args",
    [
        (get_frames, None, []),
        (get_project_or_task_completion, None, ["project1", "+"]),
        (get_project_or_task_completion, None, ["project1", "+tag1", "+"]),
        (get_project_or_task_completion, None, []),
        (get_projects, None, []),
        (get_rename_name, "project", []),
        (get_rename_name, "tag", []),
        (get_rename_types, None, []),
        (get_tags, None, []),
    ],
)
def test_completion_of_nonexisting_prefix(
    watson_df, func_to_test, rename_type, args
):
    ctx = ClickContext(obj=watson_df, params={"rename_type": rename_type})
    prefix = "NOT-EXISTING-PREFIX"
    ret_list = list(func_to_test(ctx, args, prefix))
    assert not ret_list


@pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)
@pytest.mark.parametrize(
    "func_to_test, prefix, n_expected_vals, rename_type, args",
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
        (get_rename_name, "project3", N_VARIATIONS_OF_PROJECT3, "project", []),
        (get_rename_name, "tag", N_TASKS, "tag", []),
        (get_rename_types, "ta", 1, None, []),
        (get_tags, "tag", N_TASKS, None, []),
    ],
)
def test_completion_of_existing_prefix(
    watson_df, func_to_test, prefix, n_expected_vals, rename_type, args
):
    ctx = ClickContext(obj=watson_df, params={"rename_type": rename_type})
    ret_set = set(func_to_test(ctx, args, prefix))
    assert len(ret_set) == n_expected_vals
    assert all(cur_elem.startswith(prefix) for cur_elem in ret_set)


@pytest.mark.datafiles(AUTOCOMPLETION_FRAMES_PATH)
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
