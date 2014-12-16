# -*- coding: utf-8 -*-

import datetime
import operator
import itertools

from functools import reduce

import click
import arrow

from . import watson
from .utils import format_timedelta


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
        'date': {'fg': 'cyan'}
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


class DateParamType(click.ParamType):
    name = 'date'

    def convert(self, value, param, ctx):
        if value:
            return arrow.get(value)


Date = DateParamType()


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
@click.argument('project', required=False)
@click.option('-f', '--from', 'from_', type=Date,
              default=arrow.now().replace(days=-7),
              help="The date from when the log should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', type=Date, default=arrow.now(),
              help="The date at which the log should stop (inclusive). "
              "Defaults to tomorrow.")
@click.pass_obj
def log(watson, project, from_, to):
    """
    Display a summary of the time spent on each project.

    If a project is given, the time spent on this project and
    each subproject is printed. Else, print the total for each root
    project.

    By default, the time spent the last 7 days is printed. This timespan
    can be controlled with the '--from' and '--to' arguments. The dates
    must have the format 'YEAR-MONTH-DAY', like: '2014-05-19'.

    \b
    Example:
    $ watson log
    Mon 05 May 2014 -> Mon 12 May 2014

    \b
     23h 53m 16s apollo11
      7h 06m 08s hubble
      1h 06m 53s voyager1
     12h 19m 53s voyager2

    \b
    Total: 44h 26m 10s

    \b
    $ watson log --from 2014-04-01 --to 2014-04-30  apollo11
    Tue 01 April 2014 -> Wed 30 April 2014

    \b
      1h 32m 54s apollo11
      8h 28m 09s apollo11/lander
     14h 15m 07s apollo11/lander/brakes
      9h 37m 34s apollo11/lander/parachute
     11h 04m 39s apollo11/lander/steering
      6h 23m 38s apollo11/lander/wheels
      3h 28m 44s apollo11/module
     11h 23m 27s apollo11/reactor

    \b
    Total: 66h 14m 12s
    """
    if project:
        projects = (p for p in watson.projects
                    if p == project or p.startswith(project + '/'))
        subprojects = False
    else:
        projects = (p for p in watson.projects if '/' not in p)
        subprojects = True

    if from_ > to:
        raise click.ClickException("'from' must be anterior to 'to'")

    span = watson.frames.span(from_, to)

    total = datetime.timedelta()

    click.echo("{} -> {}\n".format(
        style('date', '{:ddd DD MMMM YYYY}'.format(span.start)),
        style('date', '{:ddd DD MMMM YYYY}'.format(span.stop))
    ))

    for name in projects:
        frames = (f for f in watson.frames.for_project(name, subprojects)
                  if f in span)
        delta = reduce(
            operator.add,
            (f.stop - f.start for f in frames),
            datetime.timedelta()
        )
        total += delta

        click.echo("{} {}".format(
            style('time', '{:>12}'.format(format_timedelta(delta))),
            style('project', name)
        ))

    click.echo("\nTotal: {}".format(
        style('time', '{}'.format(format_timedelta(total)))
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
@click.argument('key', required=False, metavar='SECTION.OPTION')
@click.argument('value', required=False)
@click.option('-e', '--edit', is_flag=True,
              help="Edit the configuration file with an editor.")
@click.pass_context
def config(context, key, value, edit):
    """
    Get and set configuration options.

    If value is not provided, the content of the key is displayed. Else,
    the given value is set.

    You can edit the config file with an editor with the '--edit' option.

    \b
    Example:
    $ watson config crick.token 7e329263e329
    $ watson config crick.token
    7e329263e329
    """
    watson = context.obj
    config = watson.config

    if edit:
        click.edit(filename=watson.config_file, extension='.ini')

        try:
            watson.config = None
            watson.config
        except WatsonCliError:
            watson.config = config
            watson.save()
            raise
        return

    if not key:
        click.echo(context.get_help())
        return

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
