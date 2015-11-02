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
from .utils import format_timedelta, sorted_groupby


def style(name, element):
    def _style_tags(tags):
        if not tags:
            return ''

        return '[{}]'.format(', '.join(
            style('tag', tag) for tag in tags
        ))

    def _style_short_id(id):
        return style('id', id[:7])

    formats = {
        'project': {'fg': 'magenta'},
        'tags': _style_tags,
        'tag': {'fg': 'blue'},
        'time': {'fg': 'green'},
        'error': {'fg': 'red'},
        'date': {'fg': 'cyan'},
        'short_id': _style_short_id,
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
            date = arrow.get(value)
            # When we parse a date, we want to parse it in the timezone
            # expected by the user, so that midnight is midnight in the local
            # timezone, not in UTC. Cf issue #16.
            date.tzinfo = tz.tzlocal()
            return date


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
@click.argument('command', required=False)
@click.pass_context
def help(ctx, command):
    """
    Display help information
    """
    if not command:
        click.echo(ctx.parent.get_help())
        return

    cmd = cli.get_command(ctx, command)

    if not cmd:
        raise click.ClickException("No such command: {}".format(command))

    click.echo(cmd.get_help(ctx))


@cli.command()
@click.argument('args', nargs=-1)
@click.pass_obj
def start(watson, args):
    """
    Start monitoring the time for the given project. You can add tags
    indicating more specifically what you are working on with '+tag'.

    \b
    Example :
    $ watson start apollo11 +module +brakes
    Starting apollo11 [module, brakes] at 16:34
    """
    if watson.config.getboolean('options', 'stop_on_start'):
        try:
            frame = watson.stop()
            click.echo("Stopping project {} {}, started {}. (id: {})".format(
                style('project', frame.project),
                style('tags', frame.tags),
                style('time', frame.start.humanize()),
                style('short_id', frame.id)
            ))
        except WatsonCliError:
            pass

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
    click.echo("Starting {} {} at {}".format(
        style('project', project),
        style('tags', tags),
        style('time', "{:HH:mm}".format(current['start']))
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
    Stopping project apollo11, started a minute ago. (id: e7ccd52)
    """
    frame = watson.stop()
    click.echo("Stopping project {} {}, started {}. (id: {})".format(
        style('project', frame.project),
        style('tags', frame.tags),
        style('time', frame.start.humanize()),
        style('short_id', frame.id)
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
    click.echo("Canceling the timer for project {} {}".format(
        style('project', old['project']),
        style('tags', old['tags'])
    ))
    watson.save()


@cli.command()
@click.pass_obj
def status(watson):
    """
    Display when the current project was started and the time spent since.

    You can configure how the date and time of when the project was started are
    displayed by setting 'options.date_format' and 'options.time_format' in the
    configuration. The syntax of these formatting strings and the supported
    placeholders are the same as for the 'strftime' method of Python's
    'datetime.datetime' class.

    \b
    Example:
    $ watson status
    Project apollo11 [brakes] started seconds ago (2014-05-19 14:32:41+0100)
    $ watson config options.date_format %d.%m.%Y
    $ watson config options.time_format "at %I:%M %p"
    $ watson status
    Project apollo11 [brakes] started a minute ago (19.05.2014 at 02:32 PM)
    """
    if not watson.is_started:
        click.echo("No project started")
        return

    current = watson.current
    datefmt = watson.config.get('options', 'date_format', '%Y.%m.%d')
    timefmt = watson.config.get('options', 'time_format', '%H:%M:%S%z')
    click.echo("Project {} {} started {} ({} {})".format(
        style('project', current['project']),
        style('tags', current['tags']),
        style('time', current['start'].humanize()),
        style('date', current['start'].strftime(datefmt)),
        style('time', current['start'].strftime(timefmt))
    ))


@cli.command()
@click.option('-f', '--from', 'from_', type=Date,
              default=arrow.now().replace(days=-7),
              help="The date from when the report should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', type=Date, default=arrow.now(),
              help="The date at which the report should stop (inclusive). "
              "Defaults to tomorrow.")
@click.option('-p', '--project', 'projects', multiple=True,
              help="Reports activity only for the given project. You can add "
              "other projects by using this option several times.")
@click.option('-T', '--tag', 'tags', multiple=True,
              help="Reports activity only for frames containing the given "
              "tag. You can add several tags by using this option multiple "
              "times")
@click.pass_obj
def report(watson, from_, to, projects, tags):
    """
    Display a report of the time spent on each project.

    If a project is given, the time spent on this project
    is printed. Else, print the total for each root
    project.

    By default, the time spent the last 7 days is printed. This timespan
    can be controlled with the '--from' and '--to' arguments. The dates
    must have the format 'YEAR-MONTH-DAY', like: '2014-05-19'.

    You can limit the report to a project or a tag using the `--project` and
    `--tag` options. They can be specified several times each to add multiple
    projects or tags to the report.

    \b
    Example:
    $ watson report
    Mon 05 May 2014 -> Mon 12 May 2014

    \b
    apollo11 - 13h 22m 20s
            [brakes    7h 53m 18s]
            [module    7h 41m 41s]
            [reactor   8h 35m 50s]
            [steering 10h 33m 37s]
            [wheels   10h 11m 35s]

    \b
    hubble - 8h 54m 46s
            [camera        8h 38m 17s]
            [lens          5h 56m 22s]
            [transmission  6h 27m 07s]

    \b
    voyager1 - 11h 45m 13s
            [antenna     5h 53m 57s]
            [generators  9h 04m 58s]
            [probe      10h 14m 29s]
            [sensors    10h 30m 26s]

    \b
    voyager2 - 16h 16m 09s
            [antenna     7h 05m 50s]
            [generators 12h 20m 29s]
            [probe      12h 20m 29s]
            [sensors    11h 23m 17s]

    \b
    Total: 43h 42m 20s

    \b
    $ watson report --from 2014-04-01 --to 2014-04-30 --project apollo11
    Tue 01 April 2014 -> Wed 30 April 2014

    \b
    apollo11 - 13h 22m 20s
            [brakes    7h 53m 18s]
            [module    7h 41m 41s]
            [reactor   8h 35m 50s]
            [steering 10h 33m 37s]
            [wheels   10h 11m 35s]
    """
    if from_ > to:
        raise click.ClickException("'from' must be anterior to 'to'")

    span = watson.frames.span(from_, to)

    frames_by_project = sorted_groupby(
        watson.frames.filter(
            projects=projects or None, tags=tags or None, span=span
        ),
        operator.attrgetter('project')
    )

    total = datetime.timedelta()

    click.echo("{} -> {}\n".format(
        style('date', '{:ddd DD MMMM YYYY}'.format(span.start)),
        style('date', '{:ddd DD MMMM YYYY}'.format(span.stop))
    ))

    for project, frames in frames_by_project:
        frames = tuple(frames)
        delta = reduce(
            operator.add,
            (f.stop - f.start for f in frames),
            datetime.timedelta()
        )
        total += delta

        click.echo("{project} - {time}".format(
            time=style('time', format_timedelta(delta)),
            project=style('project', project)
        ))

        tags_to_print = sorted(
            set(tag for frame in frames for tag in frame.tags
                if tag in tags or not tags)
        )
        if tags_to_print:
            longest_tag = max(len(tag) for tag in tags_to_print or [''])

        for tag in tags_to_print:
            delta = reduce(
                operator.add,
                (f.stop - f.start for f in frames if tag in f.tags),
                datetime.timedelta()
            )

            click.echo("\t[{tag} {time}]".format(
                time=style('time', '{:>11}'.format(format_timedelta(delta))),
                tag=style('tag', '{:<{}}'.format(tag, longest_tag)),
            ))

        click.echo()

    if len(projects) > 1:
        click.echo("Total: {}".format(
            style('time', '{}'.format(format_timedelta(total)))
        ))


@cli.command()
@click.option('-f', '--from', 'from_', type=Date,
              default=arrow.now().replace(days=-7),
              help="The date from when the log should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', type=Date, default=arrow.now(),
              help="The date at which the log should stop (inclusive). "
              "Defaults to tomorrow.")
@click.option('-p', '--project', 'projects', multiple=True,
              help="Logs activity only for the given project. You can add "
              "other projects by using this option several times.")
@click.option('-T', '--tag', 'tags', multiple=True,
              help="Logs activity only for frames containing the given "
              "tag. You can add several tags by using this option multiple "
              "times")
@click.pass_obj
def log(watson, from_, to, projects, tags):
    """
    Display each recorded session during the given timespan.

    By default, the sessions from the last 7 days are printed. This timespan
    can be controlled with the '--from' and '--to' arguments. The dates
    must have the format 'YEAR-MONTH-DAY', like: '2014-05-19'.

    You can limit the log to a project or a tag using the `--project` and
    `--tag` options. They can be specified several times each to add multiple
    projects or tags to the log.

    \b
    Example:
    $ watson log --project voyager2 --project apollo11
    Thursday 08 May 2015
            f35bb24  09:26 to 10:22     56m 33s  apollo11  [reactor, brakes, steering, wheels, module]

    \b
    Wednesday 07 May 2015
            9a1325d  09:48 to 10:15     27m 29s  voyager2  [sensors, generators, probe]

    \b
    Tuesday 06 May 2015
            530768b  12:40 to 14:16  1h 35m 45s  apollo11  [wheels]
            84164f0  14:23 to 14:35     11m 37s  apollo11  [brakes, steering]

    \b
    Monday 05 May 2015
            26a2817  09:05 to 10:03     57m 12s  voyager2  [probe, generators]
            5590aca  10:51 to 14:47  3h 55m 40s  apollo11
            c32c74e  15:12 to 18:38  3h 25m 34s  voyager2  [probe, generators, sensors, antenna]

    \b
    $ watson log --from 2014-04-16 --to 2014-04-17
    Thursday 17 April 2014
            a96fcde  09:15 to 09:43     28m 11s    hubble  [lens, camera, transmission]
            5e91316  10:19 to 12:59  2h 39m 15s    hubble  [camera, transmission]
            761dd51  14:42 to 15:54  1h 11m 47s  voyager1  [antenna]

    \b
    Wednesday 16 April 2014
            02cb269  09:53 to 12:43  2h 50m 07s  apollo11  [wheels]
            1070ddb  13:48 to 16:17  2h 29m 11s  voyager1  [antenna, sensors]
    """  # noqa
    if from_ > to:
        raise click.ClickException("'from' must be anterior to 'to'")

    span = watson.frames.span(from_, to)
    frames_by_day = sorted_groupby(
        watson.frames.filter(
            projects=projects or None, tags=tags or None, span=span
        ),
        operator.attrgetter('day'), reverse=True
    )

    lines = []

    for i, (day, frames) in enumerate(frames_by_day):
        if i != 0:
            lines.append('')

        frames = sorted(frames, key=operator.attrgetter('start'))
        longest_project = max(len(frame.project) for frame in frames)

        lines.append(style('date', "{:dddd DD MMMM YYYY}".format(day)))

        lines.append('\n'.join(
            '\t{id}  {start} to {stop}  {delta:>10}  {project}  {tags}'.format(
                delta=format_timedelta(frame.stop - frame.start),
                project=style('project',
                              '{:>{}}'.format(frame.project, longest_project)),
                pad=longest_project,
                tags=style('tags', frame.tags),
                start=style('time', '{:HH:mm}'.format(frame.start)),
                stop=style('time', '{:HH:mm}'.format(frame.stop)),
                id=style('short_id', frame.id)
            )
            for frame in frames
        ))

    click.echo_via_pager('\n'.join(lines))


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
@click.pass_obj
def tags(watson):
    """
    Display the list of all the tags.

    \b
    Example:
    $ watson tags
    antenna
    brakes
    camera
    generators
    lens
    module
    probe
    reactor
    sensors
    steering
    transmission
    wheels
    """
    for tag in watson.tags:
        click.echo(style('tag', tag))


@cli.command()
@click.pass_obj
def frames(watson):
    """
    Display the list of all frame IDs.

    \b
    Example:
    $ watson frames
    f1c4815
    9d1a989
    8801ec3
    [...]
    """
    for frame in watson.frames:
        click.echo(style('short_id', frame.id))


@cli.command()
@click.argument('id', required=False)
@click.pass_obj
def edit(watson, id):
    """
    Edit a frame. You can get the id of a frame with the `watson log`
    command. If no id is given, defaults to the last recorded frame.

    The `$EDITOR` environment variable is used to detect your editor.
    """
    if not id:
        try:
            frame = watson.frames[-1]
            id = frame.id
        except IndexError:
            raise click.ClickException(
                "No frame to edit. It's time to create your first one!"
            )
    else:
        try:
            frame = watson.frames[id]
        except KeyError:
            raise click.ClickException("No frame found with id {}.".format(id))

    format = 'YYYY-MM-DD HH:mm:ss'

    text = json.dumps({
        'start': frame.start.format(format),
        'stop': frame.stop.format(format),
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
        'Edited frame for project {project} {tags}, from {start} to {stop} '
        '({delta})'.format(
            delta=format_timedelta(frame.stop - frame.start),
            project=style('project', frame.project),
            tags=style('tags', frame.tags),
            start=style('time', '{:HH:mm}'.format(frame.start)),
            stop=style('time', '{:HH:mm}'.format(frame.stop))
        )
    )


@cli.command()
@click.argument('id')
@click.option('-f', '--force', is_flag=True,
              help="Don't ask for confirmation.")
@click.pass_obj
def remove(watson, id, force):
    """
    Remove a frame.
    """
    try:
        frame = watson.frames[id]
    except KeyError:
        raise click.ClickException("No frame found with id {}.".format(id))

    if not force:
        click.confirm(
            "You are about to remove frame "
            "{project} {tags} from {start} to {stop}, continue?".format(
                project=style('project', frame.project),
                tags=style('tags', frame.tags),
                start=style('time', '{:HH:mm}'.format(frame.start)),
                stop=style('time', '{:HH:mm}'.format(frame.stop))
            ),
            abort=True
        )

    del watson.frames[id]

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
    $ watson config backend.token 7e329263e329
    $ watson config backend.token
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
    $ watson config backend.url http://localhost:4242
    $ watson config backend.token 7e329263e329
    $ watson sync
    Received 42 frames from the server
    Pushed 23 frames to the server
    """
    last_pull = arrow.utcnow()
    pulled = watson.pull()
    click.echo("Received {} frames from the server".format(len(pulled)))

    pushed = watson.push(last_pull)
    click.echo("Pushed {} frames to the server".format(len(pushed)))

    watson.last_sync = arrow.utcnow()
    watson.save()
