from .utils import create_watson, parse_tags


def _bypass_click_bug_to_ensure_watson(ctx):
    # When pallets/click#942 is fixed, this won't be needed...
    if ctx.obj is None:
        ctx.obj = create_watson()
    return ctx.obj


def get_project_or_task_completion(ctx, args, incomplete):
    """Function to autocomplete either organisations or tasks, depending on the
       shape of the current argument."""

    assert isinstance(incomplete, str)

    def get_incomplete_tag(args, incomplete):
        """Get incomplete tag from command line string."""
        cmd_line = " ".join(args + [incomplete])
        found_tags = parse_tags(cmd_line)
        return found_tags[-1] if found_tags else ""

    def fix_broken_tag_parsing(incomplete_tag):
        """
        Remove spaces from parsed tag

        The function `parse_tags` inserts a space after each character. In
        order to obtain the actual command line part, the space needs to be
        removed.
        """
        return "".join(char for char in incomplete_tag.split(" "))

    def prepend_plus(tag_suggestions):
        """
        Prepend '+' to each tag suggestion.

        For the `watson` targeted with the function
        get_project_or_task_completion, a leading plus in front of a tag is
        expected. The get_tags() suggestion generation does not include those
        as it targets other subcommands.

        In order to not destroy the current tag stub, the plus must be
        pretended.
        """
        for cur_suggestion in tag_suggestions:
            yield "+{cur_suggestion}".format(cur_suggestion=cur_suggestion)

    _bypass_click_bug_to_ensure_watson(ctx)

    project_is_completed = any(
        tok.startswith("+") for tok in args + [incomplete]
    )
    if project_is_completed:
        incomplete_tag = get_incomplete_tag(args, incomplete)
        fixed_incomplete_tag = fix_broken_tag_parsing(incomplete_tag)
        tag_suggestions = get_tags(ctx, args, fixed_incomplete_tag)
        return prepend_plus(tag_suggestions)
    else:
        return get_projects(ctx, args, incomplete)


def get_projects(ctx, args, incomplete):
    """Function to return all projects matching the prefix."""
    watson = _bypass_click_bug_to_ensure_watson(ctx)
    for cur_project in watson.projects:
        if cur_project.startswith(incomplete):
            yield cur_project


def get_rename_name(ctx, args, incomplete):
    """
    Function to return all projects or tasks matching the prefix

    Depending on the specified rename_type, either a list of projects or a list
    of tasks must be returned. This function takes care of this distinction and
    returns the appropriate names.

    If the passed in type is unknown, e.g. due to a typo, an empty completion
    is generated.
    """

    in_type = ctx.params["rename_type"]
    if in_type == "project":
        return get_projects(ctx, args, incomplete)
    elif in_type == "tag":
        return get_tags(ctx, args, incomplete)

    return []


def get_rename_types(ctx, args, incomplete):
    """Function to return all rename types matching the prefix."""
    for cur_type in "project", "tag":
        if cur_type.startswith(incomplete):
            yield cur_type


def get_tags(ctx, args, incomplete):
    """Function to return all tags matching the prefix."""
    watson = _bypass_click_bug_to_ensure_watson(ctx)
    for cur_tag in watson.tags:
        if cur_tag.startswith(incomplete):
            yield cur_tag


def get_frames(ctx, args, incomplete):
    """
    Return all matching frame IDs

    This function returns all frame IDs that match the given prefix in a
    generator. If no ID matches the prefix, it returns the empty generator.
    """
    watson = _bypass_click_bug_to_ensure_watson(ctx)

    for cur_frame in watson.frames:
        yield_candidate = cur_frame.id
        if yield_candidate.startswith(incomplete):
            yield yield_candidate
