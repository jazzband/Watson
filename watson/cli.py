# -*- coding: utf-8 -*-

import itertools

import click

from . import watson


def style(type, string):
    def _style_project(project):
        colors = itertools.cycle(('magenta', 'blue', 'yellow'))
        return '/'.join(
            click.style(p, fg=c) for p, c in zip(project.split('/'), colors)
        )

    styles = {
        'project': _style_project,
        'time': {'fg': 'green'},
        'error': {'fg': 'red'},
    }

    style = styles.get(type, {})

    if isinstance(style, dict):
        return click.style(string, **style)
    else:
        return style(string)


class WatsonCliError(click.ClickException):
    def format_message(self):
        return style('error', self.message)


watson.WatsonError = WatsonCliError


@click.group()
@click.pass_context
def cli(ctx):
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

    ctx.obj = watson.Watson()


@cli.command()
@click.argument('project', nargs=-1)
@click.pass_obj
def start(watson, project):
    """
    Start monitoring the time for the given project.

    You can specify sub-projects by separating each name by
    slashes (/) or spaces.

    \b
    Example :
    $ watson start apollo11 reactor
    Starting apollo11/reactor at 16:34
    """
    project = '/'.join(project)

    current = watson.start(project)
    click.echo("Starting {} at {}".format(
        style('project', project),
        style('time', "{:HH:mm}".format(current['start'].to('local')))
    ))
    watson.save()


@cli.command()
@click.pass_obj
def stop(watson):
    """
    Stop monitoring time for the current project

    \b
    Example:
    $ watson stop
    Stopping project apollo11/reactor, started a minute ago
    """
    old = watson.stop()
    click.echo("Stopping project {}, started {}.".format(
        style('project', old['project']),
        style('time', old['start'].humanize())
    ))
    watson.save()


@cli.command()
@click.pass_obj
def cancel(watson):
    """
    Cancel the last call to the start command. The time will
    not be recorded.
    """
    old = watson.cancel()
    click.echo("Canceling the timer for project {}".format(
        style('project', old['project'])
    ))
    watson.save()


@cli.command()
@click.pass_obj
def status(watson):
    """
    Display the time spent since the current project was started.

    \b
    Example:
    $ watson status
    Project apollo11/reactor started seconds ago
    """
    if not watson.is_started:
        click.echo("No project started")
        return

    current = watson.current
    click.echo("Project {} started {}".format(
        style('project', current['project']),
        style('time', current['start'].humanize())
    ))


@cli.command()
@click.pass_obj
def projects(watson):
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
    for project in watson.projects:
        click.echo(style('project', project))


@cli.command()
@click.argument('key')
@click.argument('value', required=False)
@click.pass_obj
def config(watson, key, value):
    """
    Get and set configuration options. The key must have the format
    'section.option'.

    If value is not provided, the content of the key is displayed. Else,
    the given value is set.

    \b
    Example:
    $ watson config crick.token 7e329263e329
    $ watson config crick.token
    7e329263e329
    """
    config = watson.config

    try:
        section, option = key.split('.')
    except ValueError:
        raise click.ClickException(
            "The key must have the format 'section.option'"
        )

    if value is None:
        if not config.has_section(section):
            raise click.ClickException("No such section {}".format(section))

        if not config.has_option(section, option):
            raise click.ClickException(
                "No such option {} in {}".format(option, section)
            )

        click.echo(config.get(section, option))
    else:
        if not config.has_section(section):
            config.add_section(section)

        config.set(section, option, value)
        watson.config = config
        watson.save()


@cli.command()
@click.option('-f', '--force', is_flag=True,
              help="Update the existing frames on the server.")
@click.pass_obj
def push(watson, force):
    """
    Push all the new frames to a Crick server.

    The URL of the server and the User Token must be defined via the
    'watson config' command.

    If you give the '-f' (or '--force') flag to the command, it will
    also update all the existing frames on the server.

    \b
    Example:
    $ watson config crick.url http://localhost:4242
    $ watson config crick.token 7e329263e329
    $ watson push

    See https://bitbucket.org/tailordev/django-crick for more information.
    """
    frames = watson.push(force)
    click.echo("{} frames pushed to the server.".format(len(frames)))
    watson.save()
