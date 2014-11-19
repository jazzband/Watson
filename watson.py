# -*- coding: utf-8 -*-

import os
import json

import arrow
import click

WATSON_FILE = os.path.join(os.path.expanduser('~'), '.watson')
WATSON_CONF = os.path.join(os.path.expanduser('~'), '.watson.conf')


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

    if not project:
        raise click.ClickException("No project given.")

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
        if name not in project['projects']:
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


@cli.command()
def projects():
    """
    Display the list of all the existing projects.

    \b
    Example:
    $ watson projects
    apollo11
    apollo11/reactor
    apollo11/module
    apollo11/lander
    hubble
    voyager1
    voyager2
    """
    watson = get_watson()

    def get_projects(project, ancestors):
        result = []

        for name, child in project.get('projects', {}).items():
            result.append(ancestors + [name])
            result += get_projects(child, ancestors + [name])

        return result

    for project in sorted(get_projects(watson, [])):
        click.echo('/'.join(project))


@cli.command()
@click.option('-f', '--force', is_flag=True,
              help="Update the existing frames on the server.")
def push(force):
    """
    Push all the new frames to a Crick server.

    The URL of the server and the User Token must be defined in a
    `.watson.conf` file placed inside your directory.

    If you give the '-f' (or '--force') flag to the command, it will
    also update all the existing frames on the server.

    \b
    Example of `.watson.conf` file:
    [crick]
    url = http://localhost:4242
    token = 7e329263e329646be79d6cc3b3af7bf48b6b1779

    See https://bitbucket.org/tailordev/django-crick for more information.
    """
    import requests

    try:
        from ConfigParser import SafeConfigParser
    except ImportError:
        from configparser import SafeConfigParser

    config = SafeConfigParser()
    config.read(WATSON_CONF)

    if 'crick' not in config or 'url' not in config['crick']:
        raise click.ClickException((
            "You must specify a remote URL by putting it in Watson's config"
            " file at '{}'").format(WATSON_CONF)
        )

    dest = config['crick']['url']
    token = config['crick']['token']

    watson = get_watson()

    def get_frames(parent, ancestors=None, existing=False):
        frames = []
        if not ancestors:
            ancestors = []

        for name, project in parent['projects'].items():
            for frame in project['frames']:
                if 'id' in frame:
                    if not existing:
                        continue
                else:
                    if existing:
                        continue

                frame['project'] = ancestors + [name]
                frames.append(frame)

            frames += get_frames(project, ancestors + [name], existing)
        return frames

    new_frames = sorted(get_frames(watson), key=lambda e: e['start'])

    if force:
        existing_frames = get_frames(watson, existing=True)
    else:
        existing_frames = []

    headers = {
        'content-type': 'application/json',
        'Authorization': "Token {}".format(token)
    }

    if new_frames:
        data = json.dumps({'frames': new_frames})
        response = requests.post(dest + '/frames/', data, headers=headers)

        if response.status_code != 201:
            raise click.ClickException(
                "An error occured with the remote server: {}".format(
                    response.json()
                )
            )

        ids = response.json()

        for frame, _id in zip(new_frames, ids):
            frame['id'] = _id
            del frame['project']

        save_watson(watson)

    if existing_frames:
        data = json.dumps({'frames': existing_frames})
        response = requests.put(dest + '/frames/', data, headers=headers)

        if response.status_code != 200:
            raise click.ClickException(
                "An error occured with the remote server: {}".format(
                    response.json()
                )
            )

    click.echo("{} frames pushed to the server.".format(len(new_frames)))

if __name__ == '__main__':
    cli()
