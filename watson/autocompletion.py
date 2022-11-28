from .utils import create_watson


def _bypass_click_bug_to_ensure_watson(ctx):
    # When pallets/click#942 is fixed, this won't be needed...
    if ctx.obj is None:
        ctx.obj = create_watson()
    return ctx.obj


def get_project_tag_combined(ctx, param, incomplete):
    """Function to autocomplete either organisations or tasks, depending on the
    shape of the current argument."""

    watson = _bypass_click_bug_to_ensure_watson(ctx)

    if ctx.params["args"]:
        # This isn't the first word, so we assume you're completing tags
        given_tags = set(ctx.params["args"][1:])
        return [
            tag
            for tag in [f"+{t}" for t in watson.tags]
            if tag.startswith(incomplete) and tag not in given_tags
        ]

    else:
        return get_projects(ctx, param, incomplete)


def get_projects(ctx, param, incomplete):
    """Function to return all projects matching the prefix."""
    watson = _bypass_click_bug_to_ensure_watson(ctx)
    # breakpoint()
    return [
        project
        for project in watson.projects
        if project.startswith(incomplete) and project not in ctx.params.get("args", [])
    ]


def get_frames(ctx, param, incomplete):
    """
    Return all matching frame IDs

    This function returns all frame IDs that match the given prefix in a
    generator. If no ID matches the prefix, it returns the empty generator.
    """
    watson = _bypass_click_bug_to_ensure_watson(ctx)

    return [frame.id for frame in watson.frames if frame.id.startswith(incomplete)]


######
## tags and projects with -T/-p


def get_option_tags(ctx, param, incomplete):
    watson = _bypass_click_bug_to_ensure_watson(ctx)
    # breakpoint()
    return [
        tag
        for tag in watson.tags
        if tag.startswith(incomplete) and tag not in ctx.params["tags"]
    ]


def get_option_projects(ctx, param, incomplete):
    watson = _bypass_click_bug_to_ensure_watson(ctx)
    # breakpoint()
    return [
        project
        for project in watson.projects
        if project.startswith(incomplete) and project not in ctx.params["projects"]
    ]


#########
## Rename


def get_rename_types(ctx, param, incomplete):
    """Function to return all rename types matching the prefix."""
    # breakpoint()
    return [
        rename_type
        for rename_type in ["project", "tag"]
        if rename_type.startswith(incomplete)
    ]


def get_rename_old_name(ctx, param, incomplete):
    watson = _bypass_click_bug_to_ensure_watson(ctx)
    items = {
        "project": watson.projects,
        "tag": watson.tags,
    }[ctx.params["rename_type"]]
    return [item for item in items if item.startswith(incomplete)]


def get_rename_new_name(ctx, param, incomplete):
    watson = _bypass_click_bug_to_ensure_watson(ctx)
    items = {
        "project": watson.projects,
        "tag": watson.tags,
    }[ctx.params["rename_type"]]
    return [
        item
        for item in items
        if item.startswith(incomplete) and item != ctx.params["old_name"]
    ]
