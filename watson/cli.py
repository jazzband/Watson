# -*- coding: utf-8 -*-

import json
import datetime
import operator
import itertools

from functools import reduce
from dateutil import tz

import click
import arrow

from . import watson
from .utils import format_timedelta


def style(name, element):
    def _style_tags(tags):
        if not tags:
            return ''

        return ' [{}]'.format(', '.join(
            style('tag', tag) for tag in tags
        ))

    formats = {
        'project': {'fg': 'magenta'},
        'tags': _style_tags,
        'tag': {'fg': 'blue'},
        'time': {'fg': 'green'},
        'error': {'fg': 'red'},
        'date': {'fg': 'cyan'},
        'id': {'fg': 'white'}
    }

    fmt = formats.get(name, {})

    if isinstance(fmt, dict):
        return click.style(element, **fmt)
    else:
        # The fmt might be a function if we need to do some computation
        return fmt(element)


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
    """
    # This is the main command group, needed by click in order
    # to handle the subcommands

    ctx.obj = watson.Watson()


@cli.command()
@click.argument('args', nargs=-1)
@click.pass_obj
def start(watson, args):
    """
    Start monitoring the time for the given project.

    \b
    Example :
    $ watson start apollo11
    Starting apollo11 at 16:34
    """
    project = ' '.join(
        itertools.takewhile(lambda s: not s.startswith('+'), args)
    )

    # Find all the tags starting by a '+', even if there are spaces in them,
    # then strip each tag and filter out the empty ones
    tags = list(filter(None, map(operator.methodcaller('strip'), (
        # We concatenate the word with the '+' to the following words
        # not starting with a '+'
        w[1:] + ' ' + ' '.join(itertools.takewhile(
            lambda s: not s.startswith('+'), args[i + 1:]
        ))
        for i, w in enumerate(args) if w.startswith('+')
    ))))  # pile of pancakes !

    current = watson.start(project, tags)
    click.echo("Starting {}{} at {}".format(
        style('project', project),
        style('tags', tags),
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
    Stopping project apollo11, started a minute ago
    """
    old = watson.stop()
    click.echo("Stopping project {}{}, started {}.".format(
        style('project', old['project']),
        style('tags', old['tags']),
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
    click.echo("Canceling the timer for project {}{}".format(
        style('project', old['project']),
        style('tags', old['tags'])
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
    Project apollo11 started seconds ago
    """
    if not watson.is_started:
        click.echo("No project started")
        return

    current = watson.current
    click.echo("Project {}{} started {}".format(
        style('project', current['project']),
        style('tags', current['tags']),
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

    If a project is given, the time spent on this project
    is printed. Else, print the total for each root
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

    \b
    Total: 1h 32m 54s
    """
    if project:
        projects = (project,)
    else:
        projects = watson.projects

    if from_ > to:
        raise click.ClickException("'from' must be anterior to 'to'")

    span = watson.frames.span(from_, to)

    total = datetime.timedelta()

    click.echo("{} -> {}\n".format(
        style('date', '{:ddd DD MMMM YYYY}'.format(span.start)),
        style('date', '{:ddd DD MMMM YYYY}'.format(span.stop))
    ))

    for name in projects:
        frames = (f for f in watson.frames.for_project(name)
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
@click.option('-f', '--from', 'from_', type=Date,
              default=arrow.now().replace(days=-7),
              help="The date from when the report should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', type=Date, default=arrow.now(),
              help="The date at which the report should stop (inclusive). "
              "Defaults to tomorrow.")
@click.pass_obj
def report(watson, from_, to):
    """
    Print a report of the time spent on projects during the given timespan.

    By default, the time spent the last 7 days is printed. This timespan
    can be controlled with the '--from' and '--to' arguments. The dates
    must have the format 'YEAR-MONTH-DAY', like: '2014-05-19'.

    \b
    Example:
    $ watson report
    Monday 05 May 2014
            09:21 to 12:39  apollo11  3h 17m 58s
            13:26 to 14:05  voyager2 39m 08s
            14:37 to 17:11  hubble  2h 33m 12s

    \b
    Tuesday 06 May 2014
            09:38 to 10:40  voyager1  1h 02m 37s
            10:48 to 11:36  hubble 48m 51s
            12:17 to 12:35  voyager2 17m 43s

    \b
    Wednesday 07 May 2014
            09:43 to 12:55  apollo11  3h 11m 37s

    \b
    Thursday 08 May 2014
            09:36 to 13:33  hubble  3h 56m 32s
            16:33 to 20:14  voyager1  3h 41m 07s

    \b
    Friday 09 May 2014
            09:30 to 13:06  voyager2  3h 36m 46s

    \b
    $ watson report --from 2014-04-16 --to 2014-04-18
    Wednesday 16 April 2014
            14:01 to 14:42  apollo11 41m 00s
            14:46 to 17:27  voyager2  2h 40m 59s

    \b
    Thursday 17 April 2014
            09:18 to 10:12  voyager2 53m 54s
            10:19 to 12:40  voyager1  2h 20m 49s
            12:51 to 14:31  hubble  1h 39m 22s
            16:46 to 18:26  apollo11  1h 39m 29s

    \b
    Friday 18 April 2014
            09:55 to 13:39  voyager1  3h 43m 51s
            14:29 to 14:45  hubble 15m 20s
            14:55 to 16:32  voyager2  1h 36m 19s
    """
    if from_ > to:
        raise click.ClickException("'from' must be anterior to 'to'")

    span = watson.frames.span(from_, to)

    for i, (day, frames) in enumerate(watson.frames.by_day(span)):
        if i != 0:
            click.echo()

        click.echo(style('date', "{:dddd DD MMMM YYYY}".format(day)))

        for frame in sorted(frames):
            click.echo(
                '\t{id}  {start} to {stop}  {project}{tags} {delta}'.format(
                    delta=format_timedelta(frame.stop - frame.start),
                    project=style('project', frame.project),
                    tags=style('tags', frame.tags),
                    start=style('time',
                                '{:HH:mm}'.format(frame.start.to('local'))),
                    stop=style('time',
                               '{:HH:mm}'.format(frame.stop.to('local'))),
                    id=style('id', frame.id[:7])
                )
            )


@cli.command()
@click.pass_obj
def projects(watson):
    """
    Display the list of all the existing projects.

    \b
    Example:
    $ watson projects
    apollo11
    hubble
    voyager1
    voyager2
    """
    for project in watson.projects:
        click.echo(style('project', project))


@cli.command()
@click.argument('id')
@click.pass_obj
def edit(watson, id):
    """
    Edit a frame. You can get the id of a frame with the `watson report`
    command.

    The `$EDITOR` environment variable is used to detect your editor.
    """
    try:
        frame = watson.frames[id]
    except KeyError:
        raise click.ClickException("No frame found with id {}.".format(id))

    format = 'YYYY-MM-DD HH:mm:ss'

    text = json.dumps({
        'start': frame.start.to('local').format(format),
        'stop': frame.stop.to('local').format(format),
        'project': frame.project,
        'tags': frame.tags,
    }, indent=4, sort_keys=True)

    output = click.edit(text, extension='.json')

    if not output:
        click.echo("No change made.")
        return

    try:
        data = json.loads(output)

        project = data['project']
        tags = data['tags']
        start = arrow.get(
            data['start'], format).replace(tzinfo=tz.tzlocal()).to('utc')
        stop = arrow.get(
            data['stop'], format).replace(tzinfo=tz.tzlocal()).to('utc')

    except (ValueError, RuntimeError) as e:
        raise click.ClickException("Error saving edited frame: {}".format(e))
    except KeyError:
        raise click.ClickException(
            "The edited frame must contain the project, start and stop keys."
        )

    watson.frames[id] = (project, start, stop, tags)
    frame = watson.frames[id]

    watson.save()

    click.echo(
        'Edited frame for project {project}{tags}, from {start} to {stop} '
        '({delta})'.format(
            delta=format_timedelta(frame.stop - frame.start).strip(),
            project=style('project', frame.project),
            tags=style('tags', frame.tags),
            start=style('time', '{:HH:mm}'.format(frame.start.to('local'))),
            stop=style('time', '{:HH:mm}'.format(frame.stop.to('local')))
        )
    )


@cli.command()
@click.argument('id')
@click.pass_obj
def remove(watson, id):
    """
    Remove a frame.
    """
    try:
        del watson.frames[id]
    except KeyError:
        raise click.ClickException("No frame found with id {}.".format(id))

    watson.save()
    click.echo("Frame deleted.")


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
@click.pass_obj
def sync(watson):
    """
    Get the frames from the server and push the new ones.

    The URL of the server and the User Token must be defined via the
    'watson config' command.

    \b
    Example:
    $ watson config crick.url http://localhost:4242
    $ watson config crick.token 7e329263e329
    $ watson sync
    Received 42 frames from the server
    Pushed 23 frames to the server

    See https://bitbucket.org/tailordev/django-crick for more information.
    """
    last_pull = arrow.utcnow()
    pulled = watson.pull()
    click.echo("Received {} frames from the server".format(len(pulled)))

    pushed = watson.push(last_pull)
    click.echo("Pushed {} frames to the server".format(len(pushed)))

    watson.last_sync = arrow.utcnow()
    watson.save()
