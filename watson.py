import os
import json

import arrow
import click

WATSON_FILE = os.path.join(os.path.expanduser('~'), '.watson')


def get_watson():
    try:
        with open(WATSON_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except ValueError:
        return {}
    else:
        raise click.FileError(
            "Impossible to open Watson file in {}".format(WATSON_FILE)
        )


def save_watson(content):
    try:
        with open(WATSON_FILE, 'w+') as f:
            return json.dump(content, f, indent=2)
    except OSError:
        raise click.FileError(
            "Impossible to open Watson file in {}".format(WATSON_FILE)
        )


@click.group()
def cli():
    pass


@cli.command()
@click.argument('project')
def start(project):
    watson = get_watson()
    start_time = arrow.utcnow()

    if watson.get('current') is not None:
        project = watson['current'].get('project', "?")
        raise click.ClickException(
            "Project {} is already started".format(project)
        )

    click.echo(
        "Starting {} at {:HH:mm:ss}".format(project, start_time.to('local'))
    )

    watson['current'] = {
        'project': project,
        'start': str(start_time)
    }

    save_watson(watson)


@cli.command()
@click.option('-m', '--message', default=None,
              help="Add a message to this frame")
def stop(message):
    watson = get_watson()
    stop_time = arrow.utcnow()
    current = watson.get('current')

    if not current or not current.get('project'):
        raise click.ClickException("No project started")

    start_time = arrow.get(current['start'])
    click.echo(
        ("Stopping project {}, started {}"
         .format(current['project'], start_time.humanize()))
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

    project['frames'].append(frame)
    del watson['current']
    save_watson(watson)


@cli.command()
def cancel():
    watson = get_watson()
    current = watson.get('current')

    if not current or not current.get('project'):
        raise click.ClickException("No project started")

    del watson['current']
    save_watson(watson)

if __name__ == '__main__':
    cli()
