# -*- coding: utf-8 -*-

import os
import json

import arrow
import click

WATSON_FILE = os.path.join(os.path.expanduser('~'), '.watson')


def get_watson():
    """
    Return the content of the current Watson file as a dict.
    If the file doesn't exist, return an empty dict.
    """
    try:
        with open(WATSON_FILE) as f:
            return json.load(f)
    except IOError:
        return {}
    except ValueError as e:
        # If we get an error because the file is empty, we ignore
        # it and return an empty dict. Otherwise, we raise
        # an exception in order to avoid corrupting the file.
        if os.path.getsize(WATSON_FILE) == 0:
            return {}
        else:
            raise click.ClickException(
                "Invalid Watson file {}: {}".format(WATSON_FILE, e)
            )
    else:
        raise click.ClickException(
            "Impossible to open Watson file in {}".format(WATSON_FILE)
        )


def save_watson(content):
    """
    Save the given dict in the Watson file. Create the file in necessary.
    """
    try:
        with open(WATSON_FILE, 'w+') as f:
            return json.dump(content, f, indent=2)
    except OSError:
        raise click.ClickException(
            "Impossible to open Watson file in {}".format(WATSON_FILE)
        )


@click.group()
def cli():
    """
    Watson is a tool aimed at helping you monitoring your time.

    You just have to tell Watson when you start working on your
    project with the `start` command, and you can stop the timer
    when you're done with the `stop` command.

    Projects can be divided in sub-projects by giving the projet and
    the name of the sub-projects to the `start` command.
    """
    # This is the main command group, needed by click in order
    # to handle the subcommands
    pass


@cli.command()
@click.argument('project', nargs=-1)
def start(project):
    """
    Start monitoring the time for the given project.

    You can specify sub-projects by separating each name by
    slashes (/) or spaces.

    \b
    Example :
    $ watson start apollo11 reactor
    Starting apollo11/reactor at 16:34
    """
    watson = get_watson()
    start_time = arrow.now()

    project = [p for e in project for p in e.split('/')]

    if watson.get('current') is not None:
        raise click.ClickException("Project {} is already started".format(
            "/".join(watson['current']['project'])
        ))

    click.echo("Starting {} at {:HH:mm}".format(
        "/".join(project), start_time.to('local')
    ))

    watson['current'] = {
        'project': project,
        'start': str(start_time)
    }

    save_watson(watson)


@cli.command()
@click.option('-m', '--message', default=None,
              help="Add a message to this frame")
def stop(message):
    """
    Stop monitoring time for the current project

    \b
    Example:
    $ watson stop
    Stopping project apollo11/reactor, started a minute ago
    """
    watson = get_watson()
    stop_time = arrow.now()
    current = watson.get('current')

    if not current or not current.get('project'):
        raise click.ClickException("No project started")

    start_time = arrow.get(current['start'])
    click.echo("Stopping project {}, started {}".format(
        "/".join(current['project']), start_time.humanize()
    ))

    if not watson.get('projects'):
        watson['projects'] = {}

    project = watson
    for name in current['project']:
        if name not in project:
            project['projects'][name] = {'frames': [], 'projects': {}}
        project = project['projects'][name]

    frame = {
        'start': current['start'],
        'stop': str(stop_time)
    }

    if message:
        frame['message'] = message

    project['frames'].append(frame)
    del watson['current']
    save_watson(watson)


@cli.command()
def cancel():
    """
    Cancel the last call to the start command. The time will
    not be recorded.
    """
    watson = get_watson()
    current = watson.get('current')

    if not current or not current.get('project'):
        raise click.ClickException("No project started")

    del watson['current']
    save_watson(watson)


@cli.command()
def status():
    """
    Display the time spent since the current project was started.

    \b
    Example:
    $ watson status
    Project apollo11/reactor started seconds ago
    """
    watson = get_watson()

    current = watson.get('current')

    if not current or not current.get('project'):
        click.echo("No project started")
        return

    click.echo("Project {} started {}".format(
        "/".join(current['project']), arrow.get(current['start']).humanize()
    ))

if __name__ == '__main__':
    cli()
