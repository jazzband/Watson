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
    except ValueError:
        return {}
    else:
        raise click.FileError(
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
        raise click.FileError(
            "Impossible to open Watson file in {}".format(WATSON_FILE)
        )


def project_name(project, subproject):
    """
    Helper to get the right display name of a project,
    regarding if were are in a subproject or not.
    """
    if subproject:
        return "{}/{}".format(project, subproject)
    else:
        return project


@click.group()
def cli():
    """
    Watson is a tool aimed at helping you monitoring your time.

    You just have to tell Watson when you start working on your
    project with the `start` command, and you can stop the timer
    when you're done with the `stop` command.

    Projects can be divided in sub-projects by giving the projet and
    the name of the sub-project to the `start` command.
    """
    # This is the main command group, needed by click in order
    # to handle the subcommands
    pass


@cli.command()
@click.argument('project')
@click.argument('subproject', required=False)
def start(project, subproject):
    """
    Start monitoring the time for the given project.

    You can specify a subproject by separating the project
    and the subproject by either a space or a `/`.

    \b
    Example :
    $ watson start apollo11/reactor
    Starting apollo11/reactor at 16:34
    """
    watson = get_watson()
    start_time = arrow.now()

    if project.count('/') == 1:
        project, subproject = project.split('/')

    if watson.get('current') is not None:
        project = watson['current'].get('project', "?")
        raise click.ClickException(
            "Project {} is already started".format(
                project_name(project, subproject)
            )
        )

    click.echo(
        ("Starting {} at {:HH:mm}"
         .format(project_name(project, subproject), start_time.to('local')))
    )

    watson['current'] = {
        'project': project,
        'start': str(start_time)
    }

    if subproject:
        watson['current']['subproject'] = subproject

    save_watson(watson)


@cli.command()
@click.option('-m', '--message', default=None,
              help="Add a message to this frame")
def stop(message):
    """
    Stop monitoring time for the current project or subproject

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
    click.echo(
        ("Stopping project {}, started {}"
         .format(
             project_name(current['project'], current.get('subproject')),
             start_time.humanize()
         ))
    )

    if not watson.get('projects'):
        watson['projects'] = {}

    project = watson['projects'].get(current['project'])

    if not project:
        project = {'frames': []}
        watson['projects'][current['project']] = project

    frame = {
        'start': current['start'],
        'stop': str(stop_time)
    }

    if message:
        frame['message'] = message

    if current.get('subproject'):
        frame['subproject'] = current['subproject']

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

    click.echo(
        ("Project {} started {}"
         .format(
             project_name(current['project'], current.get('subproject')),
             arrow.get(current['start']).humanize()
         ))
    )

if __name__ == '__main__':
    cli()
