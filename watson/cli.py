# -*- coding: utf-8 -*-

import click

from . import watson


watson.WatsonError = click.ClickException


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
    click.echo("Starting {} at {:HH:mm}".format(
        project, current['start'].to('local')
    ))
    watson.save()


@cli.command()
@click.option('-m', '--message', default=None,
              help="Add a message to this frame")
@click.pass_obj
def stop(watson, message):
    """
    Stop monitoring time for the current project

    \b
    Example:
    $ watson stop
    Stopping project apollo11/reactor, started a minute ago
    """
    old = watson.stop(message)
    click.echo("Stopping project {}, started {}".format(
        old['project'], old['start'].humanize()
    ))
    watson.save()


@cli.command()
@click.pass_obj
def cancel(watson):
    """
    Cancel the last call to the start command. The time will
    not be recorded.
    """
    watson.cancel()
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
        current['project'], current['start'].humanize()
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
    for project in watson.projects():
        click.echo(project)


@cli.command()
@click.option('-f', '--force', is_flag=True,
              help="Update the existing frames on the server.")
@click.pass_obj
def push(watson, force):
    """
    Push all the new frames to a Crick server.

    The URL of the server and the User Token must be defined in a
    `.watson.conf` file placed inside your user directory.

    If you give the '-f' (or '--force') flag to the command, it will
    also update all the existing frames on the server.

    \b
    Example of `.watson.conf` file:
    [crick]
    url = http://localhost:4242
    token = 7e329263e329646be79d6cc3b3af7bf48b6b1779

    See https://bitbucket.org/tailordev/django-crick for more information.
    """
    frames = watson.push(force)
    click.echo("{} frames pushed to the server.".format(len(frames)))
    watson.save()
