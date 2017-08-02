# -*- coding: utf-8 -*-

import datetime
import itertools
import json
import operator
import os

from dateutil import tz
from functools import reduce

import arrow
import click

from . import watson as _watson
from .frames import Frame
from .utils import (format_timedelta, get_frame_from_argument,
                    get_start_time_for_period, options, safe_save,
                    sorted_groupby, style)


class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                '`--{name}` is mutually exclusive with the following options: '
                '{options}'.format(name=self.name.replace('_', ''),
                                   options=', '
                                   .join(['`--{}`'.format(_) for _ in
                                         self.mutually_exclusive]))
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx, opts, args
        )


class WatsonCliError(click.ClickException):
    def format_message(self):
        return style('error', self.message)


_watson.WatsonError = WatsonCliError


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
@click.version_option(version=_watson.__version__, prog_name='Watson')
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
    ctx.obj = _watson.Watson(config_dir=os.environ.get('WATSON_DIR'))


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


def _start(watson, project, tags, restart=False):
    """
    Start project with given list of tags and save status.
    """
    current = watson.start(project, tags, restart=restart)
    click.echo("Starting project {} {} at {}".format(
        style('project', project),
        style('tags', current['tags']),
        style('time', "{:HH:mm}".format(current['start']))
    ))
    watson.save()


@cli.command()
@click.argument('args', nargs=-1)
@click.pass_obj
@click.pass_context
def start(ctx, watson, args):
    """
    Start monitoring time for the given project.
    You can add tags indicating more specifically what you are working on with
    `+tag`.

    If there is already a running project and the configuration option
    `options.stop_on_start` is set to a true value (`1`, `on`, `true` or
    `yes`), it is stopped before the new project is started.

    Example:

    \b
    $ watson start apollo11 +module +brakes
    Starting project apollo11 [module, brakes] at 16:34
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

    if (project and watson.is_started and
            watson.config.getboolean('options', 'stop_on_start')):
        ctx.invoke(stop)

    _start(watson, project, tags)


@cli.command()
@click.pass_obj
def stop(watson):
    """
    Stop monitoring time for the current project.

    Example:

    \b
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


@cli.command(context_settings={'ignore_unknown_options': True})
@click.option('-s/-S', '--stop/--no-stop', 'stop_', default=None,
              help="(Don't) Stop an already running project.")
@click.argument('frame', default='-1')
@click.pass_obj
@click.pass_context
def restart(ctx, watson, frame, stop_):
    """
    Restart monitoring time for a previously stopped project.

    By default, the project from the last frame, which was recorded, is
    restarted, using the same tags as recorded in that frame. You can specify
    the frame to use with an integer frame index argument or a frame ID. For
    example, to restart the second-to-last frame, pass `-2` as the frame index.

    Normally, if a project is currently started, watson will print an error and
    do nothing. If you set the configuration option `options.stop_on_restart`
    to a true value (`1`, `on`, `true` or `yes`), the current project, if any,
    will be stopped before the new frame is started. You can pass the option
    `-s` or `--stop` resp. `-S` or `--no-stop` to override the default or
    configured behaviour.

    If no previous frame exists or an invalid frame index or ID was given,
    an error is printed and no further action taken.

    Example:

    \b
    $ watson start apollo11 +module +brakes
    Starting project apollo11 [module, brakes] at 16:34
    $ watson stop
    Stopping project apollo11, started a minute ago. (id: e7ccd52)
    $ watson restart
    Starting project apollo11 [module, brakes] at 16:36
    """
    if not watson.frames and not watson.is_started:
        raise click.ClickException(
            style('error', "No frames recorded yet. It's time to create your "
                           "first one!"))

    if watson.is_started:
        if stop_ or (stop_ is None and
                     watson.config.getboolean('options', 'stop_on_restart')):
            ctx.invoke(stop)
        else:
            # Raise error here, instead of in watson.start(), otherwise
            # will give misleading error if running frame is the first one
            raise click.ClickException("{} {} {}".format(
                style('error', "Project already started:"),
                style('project', watson.current['project']),
                style('tags', watson.current['tags'])))

    frame = get_frame_from_argument(watson, frame)

    _start(watson, frame.project, frame.tags, restart=True)


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
    displayed by setting `options.date_format` and `options.time_format` in the
    configuration. The syntax of these formatting strings and the supported
    placeholders are the same as for the `strftime` method of Python's
    `datetime.datetime` class.

    Example:

    \b
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


_SHORTCUT_OPTIONS = ['year', 'month', 'week', 'day']


@cli.command()
@click.option('-c/-C', '--current/--no-current', 'current', default=None,
              help="(Don't) include currently running frame in report.")
@click.option('-f', '--from', 'from_', cls=MutuallyExclusiveOption, type=Date,
              default=arrow.now().replace(days=-7),
              mutually_exclusive=_SHORTCUT_OPTIONS,
              help="The date from when the report should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', cls=MutuallyExclusiveOption, type=Date,
              default=arrow.now(),
              mutually_exclusive=_SHORTCUT_OPTIONS,
              help="The date at which the report should stop (inclusive). "
              "Defaults to tomorrow.")
@click.option('-y', '--year', cls=MutuallyExclusiveOption, type=Date,
              flag_value=get_start_time_for_period('year'),
              mutually_exclusive=['day', 'week', 'month'],
              help='Reports activity for the current year.')
@click.option('-m', '--month', cls=MutuallyExclusiveOption, type=Date,
              flag_value=get_start_time_for_period('month'),
              mutually_exclusive=['day', 'week', 'year'],
              help='Reports activity for the current month.')
@click.option('-w', '--week', cls=MutuallyExclusiveOption, type=Date,
              flag_value=get_start_time_for_period('week'),
              mutually_exclusive=['day', 'month', 'year'],
              help='Reports activity for the current week.')
@click.option('-d', '--day', cls=MutuallyExclusiveOption, type=Date,
              flag_value=get_start_time_for_period('day'),
              mutually_exclusive=['week', 'month', 'year'],
              help='Reports activity for the current day.')
@click.option('-p', '--project', 'projects', multiple=True,
              help="Reports activity only for the given project. You can add "
              "other projects by using this option several times.")
@click.option('-T', '--tag', 'tags', multiple=True,
              help="Reports activity only for frames containing the given "
              "tag. You can add several tags by using this option multiple "
              "times")
@click.option('-j', '--json', 'format_json', is_flag=True,
              help="Format the report in JSON instead of plain text")
@click.pass_obj
def report(watson, current, from_, to, projects,
           tags, year, month, week, day, format_json):
    """
    Display a report of the time spent on each project.

    If a project is given, the time spent on this project is printed.
    Else, print the total for each root project.

    By default, the time spent the last 7 days is printed. This timespan
    can be controlled with the `--from` and `--to` arguments. The dates
    must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

    You can also use special shortcut options for easier timespan control:
    `--day` sets the report timespan to the current day (beginning at 00:00h)
    and `--year`, `--month` and `--week` to the current year, month or week
    respectively.

    You can limit the report to a project or a tag using the `--project` and
    `--tag` options. They can be specified several times each to add multiple
    projects or tags to the report.

    You can change the output format for the report from *plain text* to *JSON*
    by using the `--json` option.

    Example:

    \b
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
    \b
    $ watson report --format json
    {
        "projects": [
            {
                "name": "watson",
                "tags": [
                    {
                        "name": "export",
                        "time": 530.0
                    },
                    {
                        "name": "report",
                        "time": 530.0
                    }
                ],
                "time": 530.0
            }
        ],
        "time": 530.0,
        "timespan": {
            "from": "2016-02-21T00:00:00-08:00",
            "to": "2016-02-28T23:59:59.999999-08:00"
        }
    }
    """
    try:
        report = watson.report(from_, to, current, projects, tags,
                               year=year, month=month, week=week, day=day)
    except watson.WatsonError as e:
        raise click.ClickException(e)

    if format_json:
        click.echo(json.dumps(report, indent=4, sort_keys=True))
    else:
        click.echo('{} -> {}\n'.format(
            style('date', '{:ddd DD MMMM YYYY}'.format(
                arrow.get(report['timespan']['from'])
            )),
            style('date', '{:ddd DD MMMM YYYY}'.format(
                arrow.get(report['timespan']['to'])
            ))
         ))

        projects = report['projects']
        for project in projects:
            click.echo('{project} - {time}'.format(
                time=style('time', format_timedelta(
                    datetime.timedelta(seconds=project['time'])
                )),
                project=style('project', project['name'])
            ))

            tags = project['tags']
            if tags:
                longest_tag = max(len(tag) for tag in tags or [''])

                for tag in tags:
                    click.echo('\t[{tag} {time}]'.format(
                        time=style('time', '{:>11}'.format(format_timedelta(
                            datetime.timedelta(seconds=tag['time'])
                        ))),
                        tag=style('tag', '{:<{}}'.format(
                            tag['name'], longest_tag
                        )),
                    ))
            click.echo()

        if len(projects) > 1:
            click.echo('Total: {}'.format(
                style('time', '{}'.format(format_timedelta(
                    datetime.timedelta(seconds=report['time'])
                )))
            ))


@cli.command()
@click.option('-c/-C', '--current/--no-current', 'current', default=None,
              help="(Don't) include currently running frame in output.")
@click.option('-f', '--from', 'from_', type=Date,
              default=arrow.now().replace(days=-7),
              help="The date from when the log should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', type=Date, default=arrow.now(),
              help="The date at which the log should stop (inclusive). "
              "Defaults to tomorrow.")
@click.option('-y', '--year', cls=MutuallyExclusiveOption, type=Date,
              flag_value=get_start_time_for_period('year'),
              mutually_exclusive=['day', 'week', 'month'],
              help='Reports activity for the current year.')
@click.option('-m', '--month', cls=MutuallyExclusiveOption, type=Date,
              flag_value=get_start_time_for_period('month'),
              mutually_exclusive=['day', 'week', 'year'],
              help='Reports activity for the current month.')
@click.option('-w', '--week', cls=MutuallyExclusiveOption, type=Date,
              flag_value=get_start_time_for_period('week'),
              mutually_exclusive=['day', 'month', 'year'],
              help='Reports activity for the current week.')
@click.option('-d', '--day', cls=MutuallyExclusiveOption, type=Date,
              flag_value=get_start_time_for_period('day'),
              mutually_exclusive=['week', 'month', 'year'],
              help='Reports activity for the current day.')
@click.option('-p', '--project', 'projects', multiple=True,
              help="Logs activity only for the given project. You can add "
              "other projects by using this option several times.")
@click.option('-T', '--tag', 'tags', multiple=True,
              help="Logs activity only for frames containing the given "
              "tag. You can add several tags by using this option multiple "
              "times")
@click.pass_obj
def log(watson, current, from_, to, projects, tags, year, month, week, day):
    """
    Display each recorded session during the given timespan.

    By default, the sessions from the last 7 days are printed. This timespan
    can be controlled with the `--from` and `--to` arguments. The dates
    must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

    You can also use special shortcut options for easier timespan control:
    `--day` sets the log timespan to the current day (beginning at 00:00h)
    and `--year`, `--month` and `--week` to the current year, month or week
    respectively.

    You can limit the log to a project or a tag using the `--project` and
    `--tag` options. They can be specified several times each to add multiple
    projects or tags to the log.

    Example:

    \b
    $ watson log --project voyager2 --project apollo11
    Thursday 08 May 2015 (56m 33s)
            f35bb24  09:26 to 10:22      56m 33s  apollo11  [reactor, brakes, steering, wheels, module]
    \b
    Wednesday 07 May 2015 (27m 29s)
            9a1325d  09:48 to 10:15      27m 29s  voyager2  [sensors, generators, probe]
    \b
    Tuesday 06 May 2015 (1h 47m 22s)
            530768b  12:40 to 14:16   1h 35m 45s  apollo11  [wheels]
            84164f0  14:23 to 14:35      11m 37s  apollo11  [brakes, steering]
    \b
    Monday 05 May 2015 (8h 18m 26s)
            26a2817  09:05 to 10:03      57m 12s  voyager2  [probe, generators]
            5590aca  10:51 to 14:47   3h 55m 40s  apollo11
            c32c74e  15:12 to 18:38   3h 25m 34s  voyager2  [probe, generators, sensors, antenna]
    \b
    $ watson log --from 2014-04-16 --to 2014-04-17
    Thursday 17 April 2014 (4h 19m 13s)
            a96fcde  09:15 to 09:43      28m 11s    hubble  [lens, camera, transmission]
            5e91316  10:19 to 12:59   2h 39m 15s    hubble  [camera, transmission]
            761dd51  14:42 to 15:54   1h 11m 47s  voyager1  [antenna]
    \b
    Wednesday 16 April 2014 (5h 19m 18s)
            02cb269  09:53 to 12:43   2h 50m 07s  apollo11  [wheels]
            1070ddb  13:48 to 16:17   2h 29m 11s  voyager1  [antenna, sensors]
    """  # noqa
    for start_time in (_ for _ in [day, week, month, year]
                       if _ is not None):
        from_ = start_time

    if from_ > to:
        raise click.ClickException("'from' must be anterior to 'to'")

    if watson.current:
        if current or (current is None and
                       watson.config.getboolean('options', 'log_current')):
            cur = watson.current
            watson.frames.add(cur['project'], cur['start'], arrow.utcnow(),
                              cur['tags'], id="current")

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

        daily_total = reduce(
            operator.add,
            (frame.stop - frame.start for frame in frames)
        )

        lines.append(
            style(
                'date', "{:dddd DD MMMM YYYY} ({})".format(
                    day, format_timedelta(daily_total)
                )
            )
        )

        lines.append('\n'.join(
            '\t{id}  {start} to {stop}  {delta:>11}  {project}  {tags}'.format(
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

    Example:

    \b
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

    Example:

    \b
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

    Example:

    \b
    $ watson frames
    f1c4815
    9d1a989
    8801ec3
    [...]
    """
    for frame in watson.frames:
        click.echo(style('short_id', frame.id))


@cli.command(context_settings={'ignore_unknown_options': True})
@click.argument('id', required=False)
@click.pass_obj
def edit(watson, id):
    """
    Edit a frame.

    You can specify the frame to edit by its position or by its frame id.
    For example, to edit the second-to-last frame, pass `-2` as the frame
    index. You can get the id of a frame with the `watson log` command.

    If no id or index is given, the frame defaults to the current frame or the
    last recorded frame, if no project is currently running.

    The `$EDITOR` environment variable is used to detect your editor.
    """
    date_format = 'YYYY-MM-DD'
    time_format = 'HH:mm:ss'
    datetime_format = '{} {}'.format(date_format, time_format)
    local_tz = tz.tzlocal()

    if id:
        frame = get_frame_from_argument(watson, id)
        id = frame.id
    elif watson.is_started:
        frame = Frame(watson.current['start'], None, watson.current['project'],
                      None, watson.current['tags'])
    elif watson.frames:
        frame = watson.frames[-1]
        id = frame.id
    else:
        raise click.ClickException(
            style('error', "No frames recorded yet. It's time to create your "
                           "first one!"))

    data = {
        'start': frame.start.format(datetime_format),
        'project': frame.project,
        'tags': frame.tags,
    }

    if id:
        data['stop'] = frame.stop.format(datetime_format)

    text = json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)
    output = click.edit(text, extension='.json')

    if not output:
        click.echo("No change made.")
        return

    try:
        data = json.loads(output)
        project = data['project']
        tags = data['tags']
        start = arrow.get(data['start'], datetime_format).replace(
            tzinfo=local_tz).to('utc')
        stop = arrow.get(data['stop'], datetime_format).replace(
            tzinfo=local_tz).to('utc') if id else None
    except (ValueError, RuntimeError) as e:
        raise click.ClickException("Error saving edited frame: {}".format(e))
    except KeyError:
        raise click.ClickException(
            "The edited frame must contain the project, start and stop keys."
        )

    if id:
        watson.frames[id] = (project, start, stop, tags)
    else:
        watson.current = dict(start=start, project=project, tags=tags)

    watson.save()
    click.echo(
        'Edited frame for project {project} {tags}, from {start} to {stop} '
        '({delta})'.format(
            delta=format_timedelta(stop - start) if stop else '-',
            project=style('project', project),
            tags=style('tags', tags),
            start=style(
                'time',
                start.to(local_tz).format(time_format)
            ),
            stop=style(
                'time',
                stop.to(local_tz).format(time_format) if stop else '-'
            )
        )
    )


@cli.command(context_settings={'ignore_unknown_options': True})
@click.argument('id')
@click.option('-f', '--force', is_flag=True,
              help="Don't ask for confirmation.")
@click.pass_obj
def remove(watson, id, force):
    """
    Remove a frame. You can specify the frame either by id or by position
    (ex: `-1` for the last frame).
    """
    frame = get_frame_from_argument(watson, id)
    id = frame.id

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

    You can edit the config file with an editor with the `--edit` option.

    Example:

    \b
    $ watson config backend.token 7e329263e329
    $ watson config backend.token
    7e329263e329
    """
    watson = context.obj
    wconfig = watson.config

    if edit:
        try:
            with open(watson.config_file) as fp:
                rawconfig = fp.read()
        except (IOError, OSError):
            rawconfig = ''

        newconfig = click.edit(text=rawconfig, extension='.ini')

        if newconfig:
            safe_save(watson.config_file, newconfig)

        try:
            watson.config = None
            watson.config  # triggers reloading config from file
        except _watson.ConfigurationError as exc:
            watson.config = wconfig
            watson.save()
            raise WatsonCliError(str(exc))
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
        if not wconfig.has_section(section):
            raise click.ClickException("No such section {}".format(section))

        if not wconfig.has_option(section, option):
            raise click.ClickException(
                "No such option {} in {}".format(option, section)
            )

        click.echo(wconfig.get(section, option))
    else:
        if not wconfig.has_section(section):
            wconfig.add_section(section)

        wconfig.set(section, option, value)
        watson.config = wconfig
        watson.save()


@cli.command()
@click.pass_obj
def sync(watson):
    """
    Get the frames from the server and push the new ones.

    The URL of the server and the User Token must be defined via the
    `watson config` command.

    Example:

    \b
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


@cli.command()
@click.argument('frames_with_conflict', type=click.Path(exists=True))
@click.option('-f', '--force', 'force', is_flag=True,
              help="If specified, then the merge will automatically "
              "be performed.")
@click.pass_obj
def merge(watson, frames_with_conflict, force):
    """
    Perform a merge of the existing frames with a conflicting frames file.

    When storing the frames on a file hosting service, there is the
    possibility that the frame file goes out-of-sync due to one or
    more of the connected clients going offline. This can cause the
    frames to diverge.

    If the `--force` command is specified, the merge operation
    will automatically be performed.

    The only argument is a path to the the conflicting `frames` file.

    Merge will output statistics about the merge operation.

    Example:

    \b
    $ watson merge frames-with-conflicts
    120 frames will be left unchanged
    12  frames will be merged
    3   frame conflicts need to be resolved

    To perform a merge operation, the user will be prompted to
    select the frame they would like to keep.

    Example:

    \b
    $ watson merge frames-with-conflicts --force
    120 frames will be left unchanged
    12  frames will be merged
    3   frame conflicts need to be resolved
    Will resolve conflicts:
    frame 8804872:
    < {
    <     "project": "tailordev",
    <     "start": "2015-07-28 09:33:33",
    <     "stop": "2015-07-28 10:39:36",
    <     "tags": [
    <         "intern",
    <         "daily-meeting"
    <     ]
    < }
    ---
    > {
    >     "project": "tailordev",
    >     "start": "2015-07-28 09:33:33",
    >     "stop": "**2015-07-28 11:39:36**",
    >     "tags": [
    >         "intern",
    >         "daily-meeting"
    >     ]
    > }
    Select the frame you want to keep: left or right? (L/r)
    """
    original_frames = watson.frames
    conflicting, merging = watson.merge_report(frames_with_conflict)

    # find the length of the largest returned list, then get the number of
    # digits of this length
    dig = len(str(max(len(original_frames), len(merging), len(conflicting))))

    click.echo("{:<{width}} frames will be left unchanged".format(
        len(original_frames) - len(conflicting), width=dig))
    click.echo("{:<{width}} frames will be merged".format(
        len(merging), width=dig))
    click.echo("{:<{width}} frames will need to be resolved".format(
        len(conflicting), width=dig))

    # No frames to resolve or merge.
    if not conflicting and not merging:
        return

    # Confirm user would like to merge
    if not force and not click.confirm("Do you want to continue?"):
        return

    if conflicting:
        click.echo("Will resolve conflicts:")

    date_format = 'YYYY-MM-DD HH:mm:ss'

    for conflict_frame in conflicting:
        original_frame = original_frames[conflict_frame.id]

        # Print original frame
        original_frame_data = {
            'project': original_frame.project,
            'start': original_frame.start.format(date_format),
            'stop': original_frame.stop.format(date_format),
            'tags': original_frame.tags
        }
        click.echo("frame {}:".format(style('short_id', original_frame.id)))
        click.echo("{}".format('\n'.join('<' + line for line in json.dumps(
            original_frame_data, indent=4, ensure_ascii=False).splitlines())))
        click.echo("---")

        # make a copy of the namedtuple
        conflict_frame_copy = conflict_frame._replace()

        # highlight conflicts
        if conflict_frame.project != original_frame.project:
            project = '**' + str(conflict_frame.project) + '**'
            conflict_frame_copy = conflict_frame_copy._replace(project=project)

        if conflict_frame.start != original_frame.start:
            start = '**' + str(conflict_frame.start.format(date_format)) + '**'
            conflict_frame_copy = conflict_frame_copy._replace(start=start)

        if conflict_frame.stop != original_frame.stop:
            stop = '**' + str(conflict_frame.stop.format(date_format)) + '**'
            conflict_frame_copy = conflict_frame_copy._replace(stop=stop)

        for idx, tag in enumerate(conflict_frame.tags):
            if tag not in original_frame.tags:
                conflict_frame_copy.tags[idx] = '**' + str(tag) + '**'

        # Print conflicting frame
        conflict_frame_data = {
            'project': conflict_frame_copy.project,
            'start': conflict_frame_copy.start.format(date_format),
            'stop': conflict_frame_copy.stop.format(date_format),
            'tags': conflict_frame_copy.tags
        }
        click.echo("{}".format('\n'.join('>' + line for line in json.dumps(
            conflict_frame_data, indent=4, ensure_ascii=False).splitlines())))
        resp = click.prompt(
            "Select the frame you want to keep: left or right? (L/r)",
            value_proc=options(['L', 'r']))

        if resp == 'r':
            # replace original frame with conflicting frame
            original_frames[conflict_frame.id] = conflict_frame

    # merge in any non-conflicting frames
    for frame in merging:
        start, stop, project, id, tags, updated_at = frame.dump()
        original_frames.add(project, start, stop, tags=tags, id=id,
                            updated_at=updated_at)

    watson.frames = original_frames
    watson.frames.changed = True
    watson.save()


@cli.command()
@click.argument('type', required=True)
@click.argument('old_name', required=True)
@click.argument('new_name', required=True)
@click.pass_obj
def rename(watson, type, old_name, new_name):
    """
    Rename a project or tag.

    Example:

    \b
    $ watson rename project read-python-intro learn-python
    Renamed project "read-python-intro" to "learn-python"
    $ watson rename tag company-meeting meeting
    Renamed tag "company-meeting" to "meeting"

    """

    # input validation
    if type not in ['project', 'tag']:
        raise click.ClickException(style(
            'error',
            'You have to call rename with "project" or "tag"'
        ))

    if type == 'tag':
        if old_name not in watson.tags:
            raise click.ClickException(style(
                'error',
                'Tag "%s" does not exist' % old_name
            ))

        # rename tag
        for frame in watson.frames:
            if old_name in frame.tags:
                watson.frames[frame.id] = frame._replace(
                    tags=[new_name if t == old_name else t for t in frame.tags]
                )
        click.echo('Renamed tag "%s" to "%s"' % (old_name, new_name))
    if type == 'project':
        if old_name not in watson.projects:
            raise click.ClickException(style(
                'error',
                'Project "%s" does not exist' % old_name
            ))

        # rename project
        for frame in watson.frames:
            if frame.project == old_name:
                watson.frames[frame.id] = frame._replace(project=new_name)
        click.echo('Renamed project "%s" to "%s"' % (old_name, new_name))

    watson.frames.changed = True
    watson.save()
