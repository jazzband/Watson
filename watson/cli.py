import datetime
import itertools
import json
import operator
import os
from dateutil import tz
from functools import reduce, wraps

import arrow
import click
from click_didyoumean import DYMGroup

import watson as _watson
from .autocompletion import (
    get_frames,
    get_project_or_task_completion,
    get_projects,
    get_rename_name,
    get_rename_types,
    get_tags,
)
from .frames import Frame
from .utils import (
    apply_weekday_offset,
    build_csv,
    confirm_project,
    confirm_tags,
    create_watson,
    flatten_report_for_csv,
    format_timedelta,
    frames_to_csv,
    frames_to_json,
    get_frame_from_argument,
    get_start_time_for_period,
    options, safe_save,
    sorted_groupby,
    style,
    parse_tags,
    json_arrow_encoder,
)


class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.name in opts:
            if self.mutually_exclusive.intersection(opts):
                self._raise_exclusive_error()
            if self.multiple and len(set(opts[self.name])) > 1:
                self._raise_exclusive_error()
        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx, opts, args
        )

    def _raise_exclusive_error(self):
        # Use self.opts[-1] instead of self.name to handle options with a
        # different internal name.
        self.mutually_exclusive.add(self.opts[-1].strip('-'))
        raise click.ClickException(
            style(
                'error',
                'The following options are mutually exclusive: '
                '{options}'.format(options=', '.join(
                    ['`--{}`'.format(_) for _ in self.mutually_exclusive]))))


def local_tz_info() -> datetime.tzinfo:
    """Get the local time zone object, respects the TZ env variable."""
    timezone = os.environ.get("TZ", None)
    # If timezone is None or an empty string, gettz returns the local time
    tzinfo = tz.gettz(timezone)
    # gettz returns None if the timezone passed to gettz is invalid
    if tzinfo is None:
        raise click.ClickException(
            f"Invalid timezone {timezone} specified, "
            "please set the TZ environment variable with"
            " a valid timezone."
        )
    return tzinfo


class DateTimeParamType(click.ParamType):
    name = 'datetime'

    def convert(self, value, param, ctx) -> arrow:
        if value:
            date = self._parse_multiformat(value)
            if date is None:
                raise click.UsageError(
                    "Could not match value '{}' to any supported date format"
                    .format(value)
                )
            # When we parse a date, we want to parse it in the timezone
            # expected by the user, so that midnight is midnight in the local
            # timezone, or respect the TZ environment variable not in UTC.
            # Cf issue #16.
            date = date.replace(tzinfo=local_tz_info())
            # Add an offset to match the week beginning specified in the
            # configuration
            if param.name == "week":
                week_start = ctx.obj.config.get(
                    "options", "week_start", "monday")
                date = apply_weekday_offset(
                    start_time=date, week_start=week_start)
            return date

    def _parse_multiformat(self, value) -> arrow:
        date = None
        for fmt in (None, 'HH:mm:ss', 'HH:mm'):
            try:
                if fmt is None:
                    date = arrow.get(value)
                else:
                    date = arrow.get(value, fmt)
                    date = arrow.now().replace(
                        hour=date.hour,
                        minute=date.minute,
                        second=date.second
                    )
                break
            except (ValueError, TypeError):
                pass
        return date


DateTime = DateTimeParamType()


def catch_watson_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except _watson.WatsonError as e:
            raise click.ClickException(style('error', str(e)))
    return wrapper


@click.group(cls=DYMGroup)
@click.version_option(version=_watson.__version__, prog_name='Watson')
@click.option('--color/--no-color', 'color', default=None,
              help="(Don't) color output.")
@click.pass_context
def cli(ctx, color):
    """
    Watson is a tool aimed at helping you monitoring your time.

    You just have to tell Watson when you start working on your
    project with the `start` command, and you can stop the timer
    when you're done with the `stop` command.
    """

    if color is not None:
        ctx.color = True if color else False

    # This is the main command group, needed by click in order
    # to handle the subcommands
    ctx.obj = create_watson()


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


def _start(watson, project, tags, restart=False, start_at=None, gap=True):
    """
    Start project with given list of tags and save status.
    """
    current = watson.start(project, tags, restart=restart, start_at=start_at,
                           gap=gap,)
    click.echo("Starting project {}{} at {}".format(
        style('project', project),
        (" " if current['tags'] else "") + style('tags', current['tags']),
        style('time', "{:HH:mm}".format(current['start']))
    ))
    watson.save()


@cli.command()
@click.option('--at', 'at_', type=DateTime, default=None,
              cls=MutuallyExclusiveOption, mutually_exclusive=['gap_'],
              help=('Start frame at this time. Must be in '
                    '(YYYY-MM-DDT)?HH:MM(:SS)? format.'))
@click.option('-g/-G', '--gap/--no-gap', 'gap_', is_flag=True, default=True,
              cls=MutuallyExclusiveOption, mutually_exclusive=['at_'],
              help=("(Don't) leave gap between end time of previous project "
                    "and start time of the current."))
@click.argument('args', nargs=-1,
                shell_complete=get_project_or_task_completion)
@click.option('-c', '--confirm-new-project', is_flag=True, default=False,
              help="Confirm addition of new project.")
@click.option('-b', '--confirm-new-tag', is_flag=True, default=False,
              help="Confirm creation of new tag.")
@click.pass_obj
@click.pass_context
@catch_watson_error
def start(ctx, watson, confirm_new_project, confirm_new_tag, args, at_,
          gap_=True):
    """
    Start monitoring time for the given project.
    You can add tags indicating more specifically what you are working on with
    `+tag`.

    If there is already a running project and the configuration option
    `options.stop_on_start` is set to a true value (`1`, `on`, `true`, or
    `yes`), it is stopped before the new project is started.

    If `--at` option is given, the provided starting time is used. The
    specified time must be after the end of the previous frame and must not be
    in the future. If there is a current frame running, it will be stopped at
    the provided time.

    Example:

    \b
    $ watson start --at 13:37
    Starting project apollo11 at 13:37

    If the `--no-gap` flag is given, the start time of the new project is set
    to the stop time of the most recently stopped project.

    Example:

    \b
    $ watson start apollo11 +module +brakes --no-gap
    Starting project apollo11 [module, brakes] at 16:34
    """
    project = ' '.join(
        itertools.takewhile(lambda s: not s.startswith('+'), args)
    )
    if not project:
        raise click.ClickException("No project given.")

    # Confirm creation of new project if that option is set
    if (watson.config.getboolean('options', 'confirm_new_project') or
            confirm_new_project):
        confirm_project(project, watson.projects)

    # Parse all the tags
    tags = parse_tags(args)

    # Confirm creation of new tag(s) if that option is set
    if (watson.config.getboolean('options', 'confirm_new_tag') or
            confirm_new_tag):
        confirm_tags(tags, watson.tags)

    if project and watson.is_started and not gap_:
        current = watson.current
        errmsg = ("Project '{}' is already started and '--no-gap' is passed. "
                  "Please stop manually.")
        raise click.ClickException(
            style(
                'error', errmsg.format(current['project'])
            )
        )

    if (project and watson.is_started and
            watson.config.getboolean('options', 'stop_on_start')):
        ctx.invoke(stop, at_=at_)

    _start(watson, project, tags, start_at=at_, gap=gap_)


@cli.command(context_settings={'ignore_unknown_options': True})
@click.option('--at', 'at_', type=DateTime, default=None,
              help=('Stop frame at this time. Must be in '
                    '(YYYY-MM-DDT)?HH:MM(:SS)? format.'))
@click.pass_obj
@catch_watson_error
def stop(watson, at_):
    """
    Stop monitoring time for the current project.

    If `--at` option is given, the provided stopping time is used. The
    specified time must be after the beginning of the to-be-ended frame and must
    not be in the future.

    Example:

    \b
    $ watson stop --at 13:37
    Stopping project apollo11, started an hour ago and stopped 30 minutes ago. (id: e9ccd52) # noqa: E501
    """
    frame = watson.stop(stop_at=at_)
    output_str = "Stopping project {}{}, started {} and stopped {}. (id: {})"
    click.echo(output_str.format(
        style('project', frame.project),
        (" " if frame.tags else "") + style('tags', frame.tags),
        style('time', frame.start.humanize()),
        style('time', frame.stop.humanize()),
        style('short_id', frame.id),
    ))
    watson.save()


@cli.command(context_settings={'ignore_unknown_options': True})
@click.option('--at', 'at_', type=DateTime, default=None,
              cls=MutuallyExclusiveOption, mutually_exclusive=['gap_'],
              help=('Start frame at this time. Must be in '
                    '(YYYY-MM-DDT)?HH:MM(:SS)? format.'))
@click.option('-g/-G', '--gap/--no-gap', 'gap_', is_flag=True, default=True,
              cls=MutuallyExclusiveOption, mutually_exclusive=['at_'],
              help=("(Don't) leave gap between end time of previous project "
                    "and start time of the current."))
@click.option('-s/-S', '--stop/--no-stop', 'stop_', default=None,
              help="(Don't) Stop an already running project.")
@click.argument('id', default='-1', shell_complete=get_frames)
@click.pass_obj
@click.pass_context
@catch_watson_error
def restart(ctx, watson, id, stop_, at_, gap_=True):
    """
    Restart monitoring time for a previously stopped project.

    By default, the project from the last frame, which was recorded, is
    restarted, using the same tags as recorded in that frame. You can specify
    the frame to use with an integer frame index argument or a frame ID. For
    example, to restart the second-to-last frame, pass `-2` as the frame index.

    Normally, if a project is currently started, Watson will print an error and
    do nothing. If you set the configuration option `options.stop_on_restart`
    to a true value (`1`, `on`, `true`, or `yes`), the current project, if any,
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

    If the `--no-gap` flag is given, the start time of the new project is set
    to the stop time of the most recently stopped project.
    """
    if not watson.frames and not watson.is_started:
        raise click.ClickException(
            style('error', "No frames recorded yet. It's time to create your "
                           "first one!"))

    if watson.is_started and not gap_:
        current = watson.current
        errmsg = ("Project '{}' is already started and '--no-gap' is passed. "
                  "Please stop manually.")
        raise click.ClickException(
            style(
                'error', errmsg.format(current['project'])
            )
        )

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

    frame = get_frame_from_argument(watson, id)

    _start(watson, frame.project, frame.tags, restart=True, start_at=at_,
           gap=gap_)


@cli.command()
@click.pass_obj
@catch_watson_error
def cancel(watson):
    """
    Cancel the last call to the start command. The time will
    not be recorded.
    """
    old = watson.cancel()
    click.echo("Canceling the timer for project {}{}".format(
        style('project', old['project']),
        (" " if old['tags'] else "") + style('tags', old['tags'])
    ))
    watson.save()


@cli.command()
@click.option('-p', '--project', is_flag=True,
              help="only output project")
@click.option('-t', '--tags', is_flag=True,
              help="only show tags")
@click.option('-e', '--elapsed', is_flag=True,
              help="only show time elapsed")
@click.pass_obj
@catch_watson_error
def status(watson, project, tags, elapsed):
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
        click.echo("No project started.")
        return

    current = watson.current

    if project:
        click.echo("{}".format(
            style('project', current['project']),
        ))
        return

    if tags:
        click.echo("{}".format(
            style('tags', current['tags'])
        ))
        return

    if elapsed:
        click.echo("{}".format(
            style('time', current['start'].humanize())
        ))
        return

    datefmt = watson.config.get('options', 'date_format', '%Y.%m.%d')
    timefmt = watson.config.get('options', 'time_format', '%H:%M:%S%z')
    click.echo("Project {}{} started {} ({} {})".format(
        style('project', current['project']),
        (" " if current['tags'] else "") + style('tags', current['tags']),
        style('time', current['start'].humanize()),
        style('date', current['start'].strftime(datefmt)),
        style('time', current['start'].strftime(timefmt))
    ))


_SHORTCUT_OPTIONS = ['all', 'year', 'month', 'luna', 'week', 'day']
_SHORTCUT_OPTIONS_VALUES = {
    k: get_start_time_for_period(k) for k in _SHORTCUT_OPTIONS
}


@cli.command()
@click.option('-c/-C', '--current/--no-current', 'current', default=None,
              help="(Don't) include currently running frame in report.")
@click.option('-f', '--from', 'from_', cls=MutuallyExclusiveOption,
              type=DateTime, default=arrow.now().shift(days=-7),
              mutually_exclusive=_SHORTCUT_OPTIONS,
              help="The date from when the report should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', cls=MutuallyExclusiveOption, type=DateTime,
              default=arrow.now(),
              mutually_exclusive=_SHORTCUT_OPTIONS,
              help="The date at which the report should stop (inclusive). "
              "Defaults to tomorrow.")
@click.option('-y', '--year', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['year'],
              mutually_exclusive=['day', 'week', 'luna', 'month', 'all'],
              help='Reports activity for the current year.')
@click.option('-m', '--month', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['month'],
              mutually_exclusive=['day', 'week', 'luna', 'year', 'all'],
              help='Reports activity for the current month.')
@click.option('-l', '--luna', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['luna'],
              mutually_exclusive=['day', 'week', 'month', 'year', 'all'],
              help='Reports activity for the current moon cycle.')
@click.option('-w', '--week', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['week'],
              mutually_exclusive=['day', 'month', 'luna', 'year', 'all'],
              help='Reports activity for the current week.')
@click.option('-d', '--day', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['day'],
              mutually_exclusive=['week', 'month', 'luna', 'year', 'all'],
              help='Reports activity for the current day.')
@click.option('-a', '--all', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['all'],
              mutually_exclusive=['day', 'week', 'month', 'luna', 'year'],
              help='Reports all activities.')
@click.option('-p', '--project', 'projects', shell_complete=get_projects,
              multiple=True,
              help="Reports activity only for the given project. You can add "
              "other projects by using this option several times.")
@click.option('-T', '--tag', 'tags', shell_complete=get_tags, multiple=True,
              help="Reports activity only for frames containing the given "
              "tag. You can add several tags by using this option multiple "
              "times")
@click.option('--ignore-project', 'ignore_projects', multiple=True,
              help="Reports activity for all projects but the given ones. You "
              "can ignore several projects by using the option multiple "
              "times. Any given project will be ignored")
@click.option('--ignore-tag', 'ignore_tags', multiple=True,
              help="Reports activity for all tags but the given ones. You can "
              "ignore several tags by using the option multiple times. Any "
              "given tag will be ignored")
@click.option('-j', '--json', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='json', mutually_exclusive=['csv'],
              help="Format output in JSON instead of plain text")
@click.option('-s', '--csv', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='csv', mutually_exclusive=['json'],
              help="Format output in CSV instead of plain text")
@click.option('--plain', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='plain', mutually_exclusive=['json', 'csv'],
              default=True, hidden=True,
              help="Format output in plain text (default)")
@click.option('-g/-G', '--pager/--no-pager', 'pager', default=None,
              help="(Don't) view output through a pager.")
@click.pass_obj
@catch_watson_error
def report(watson, current, from_, to, projects, tags, ignore_projects,
           ignore_tags, year, month, week, day, luna, all, output_format,
           pager, aggregated=False, include_partial_frames=True):
    """
    Display a report of the time spent on each project.

    If a project is given, the time spent on this project is printed.
    Else, print the total for each root project.

    By default, the time spent the last 7 days is printed. This timespan
    can be controlled with the `--from` and `--to` arguments. The dates
    must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

    You can also use special shortcut options for easier timespan control:
    `--day` sets the report timespan to the current day (beginning at `00:00h`)
    and `--year`, `--month` and `--week` to the current year, month, or week,
    respectively.
    The shortcut `--luna` sets the timespan to the current moon cycle with
    the last full moon marking the start of the cycle.

    You can limit the report to a project or a tag using the `--project`,
    `--tag`, `--ignore-project` and `--ignore-tag` options. They can be
    specified several times each to add or ignore multiple projects or
    tags to the report.

    If you are outputting to the terminal, you can selectively enable a pager
    through the `--pager` option.

    You can change the output format for the report from *plain text* to *JSON*
    using the `--json` option or to *CSV* using the `--csv` option. Only one
    of these two options can be used at once.

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
    $ watson report --json
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
    \b
    $ watson report --from 2014-04-01 --to 2014-04-30 --project apollo11 --csv
    from,to,project,tag,time
    2014-04-01 00:00:00,2014-04-30 23:59:59,apollo11,,48140.0
    2014-04-01 00:00:00,2014-04-30 23:59:59,apollo11,brakes,28421.0
    2014-04-01 00:00:00,2014-04-30 23:59:59,apollo11,module,27701.0
    2014-04-01 00:00:00,2014-04-30 23:59:59,apollo11,reactor,30950.0
    2014-04-01 00:00:00,2014-04-30 23:59:59,apollo11,steering,38017.0
    2014-04-01 00:00:00,2014-04-30 23:59:59,apollo11,wheels,36695.0
    """

    # if the report is an aggregate report, add whitespace using this
    # aggregate tab which will be prepended to the project name
    if aggregated:
        tab = '  '
    else:
        tab = ''

    report = watson.report(from_, to, current, projects, tags,
                           ignore_projects, ignore_tags,
                           year=year, month=month, week=week, day=day,
                           luna=luna, all=all,
                           include_partial_frames=include_partial_frames)

    if 'json' in output_format and not aggregated:
        click.echo(json.dumps(report, indent=4, sort_keys=True,
                              default=json_arrow_encoder))
        return
    elif 'csv' in output_format and not aggregated:
        click.echo(build_csv(flatten_report_for_csv(report)))
        return
    elif 'plain' not in output_format and aggregated:
        return report

    lines = []
    # use the pager, or print directly to the terminal
    if pager or (pager is None and
                 watson.config.getboolean('options', 'pager', True)):

        def _print(line):
            lines.append(line)

        def _final_print(lines):
            click.echo_via_pager('\n'.join(lines))
    elif aggregated:

        def _print(line):
            lines.append(line)

        def _final_print(lines):
            pass
    else:

        def _print(line):
            click.echo(line)

        def _final_print(lines):
            pass

    # handle special title formatting for aggregate reports
    if aggregated:
        _print('{} - {}'.format(
            style('date', '{:ddd DD MMMM YYYY}'.format(
                report['timespan']['from']
            )),
            style('time', '{}'.format(format_timedelta(
                datetime.timedelta(seconds=report['time'])
            )))
        ))

    else:
        _print('{} -> {}\n'.format(
            style('date', '{:ddd DD MMMM YYYY}'.format(
                report['timespan']['from']
            )),
            style('date', '{:ddd DD MMMM YYYY}'.format(
                report['timespan']['to']
            ))
        ))

    projects = report['projects']

    for project in projects:
        _print('{tab}{project} - {time}'.format(
            tab=tab,
            time=style('time', format_timedelta(
                datetime.timedelta(seconds=project['time'])
            )),
            project=style('project', project['name'])
        ))

        tags = project['tags']
        if tags:
            longest_tag = max(len(tag) for tag in tags or [''])

            for tag in tags:
                _print('\t[{tag} {time}]'.format(
                    time=style('time', '{:>11}'.format(format_timedelta(
                        datetime.timedelta(seconds=tag['time'])
                    ))),
                    tag=style('tag', '{:<{}}'.format(
                        tag['name'], longest_tag
                    )),
                ))
        _print("")

    # if this is a report invoked from `aggregate` return the lines; do not
    # show total time
    if aggregated:
        return lines

    _print('Total: {}'.format(
        style('time', '{}'.format(format_timedelta(
            datetime.timedelta(seconds=report['time'])
        )))
    ))

    _final_print(lines)


@cli.command()
@click.option('-c/-C', '--current/--no-current', 'current', default=None,
              help="(Don't) include currently running frame in report.")
@click.option('-f', '--from', 'from_', cls=MutuallyExclusiveOption,
              type=DateTime, default=arrow.now().shift(days=-7),
              mutually_exclusive=_SHORTCUT_OPTIONS,
              help="The date from when the report should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', cls=MutuallyExclusiveOption, type=DateTime,
              default=arrow.now(),
              mutually_exclusive=_SHORTCUT_OPTIONS,
              help="The date at which the report should stop (inclusive). "
              "Defaults to tomorrow.")
@click.option('-p', '--project', 'projects', shell_complete=get_projects,
              multiple=True,
              help="Reports activity only for the given project. You can add "
              "other projects by using this option several times.")
@click.option('-T', '--tag', 'tags', shell_complete=get_tags, multiple=True,
              help="Reports activity only for frames containing the given "
              "tag. You can add several tags by using this option multiple "
              "times")
@click.option('-j', '--json', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='json', mutually_exclusive=['csv'],
              help="Format output in JSON instead of plain text")
@click.option('-s', '--csv', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='csv', mutually_exclusive=['json'],
              help="Format output in CSV instead of plain text")
@click.option('--plain', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='plain', mutually_exclusive=['json', 'csv'],
              default=True, hidden=True,
              help="Format output in plain text (default)")
@click.option('-g/-G', '--pager/--no-pager', 'pager', default=None,
              help="(Don't) view output through a pager.")
@click.pass_obj
@click.pass_context
@catch_watson_error
def aggregate(ctx, watson, current, from_, to, projects, tags, output_format,
              pager):
    """
    Display a report of the time spent on each project aggregated by day.

    If a project is given, the time spent on this project is printed.
    Else, print the total for each root project.

    By default, the time spent the last 7 days is printed. This timespan
    can be controlled with the `--from` and `--to` arguments. The dates
    must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

    You can limit the report to a project or a tag using the `--project` and
    `--tag` options. They can be specified several times each to add multiple
    projects or tags to the report.

    If you are outputting to the terminal, you can selectively enable a pager
    through the `--pager` option.

    You can change the output format from *plain text* to *JSON* using the
    `--json` option or to *CSV* using the `--csv` option. Only one of these
    two options can be used at once.


    Example:

    \b
    $ watson aggregate
    Wed 14 November 2018 - 5h 42m 22s
      watson - 5h 42m 22s
            [features     34m 06s]
            [docs  5h 08m 16s]
    \b
    Thu 15 November 2018 - 00s
    \b
    Fri 16 November 2018 - 00s
    \b
    Sat 17 November 2018 - 00s
    \b
    Sun 18 November 2018 - 00s
    \b
    Mon 19 November 2018 - 5h 58m 52s
      watson - 5h 58m 52s
            [features  1h 12m 03s]
            [docs  4h 46m 49s]
    \b
    Tue 20 November 2018 - 2h 50m 35s
      watson - 2h 50m 35s
            [features     15m 17s]
            [docs  1h 37m 43s]
            [website     57m 35s]
    \b
    Wed 21 November 2018 - 01m 17s
      watson - 01m 17s
            [docs     01m 17s]
    \b
    $ watson aggregate --csv
    from,to,project,tag,time
    2018-11-14 00:00:00,2018-11-14 23:59:59,watson,,20542.0
    2018-11-14 00:00:00,2018-11-14 23:59:59,watson,features,2046.0
    2018-11-14 00:00:00,2018-11-14 23:59:59,watson,docs,18496.0
    2018-11-19 00:00:00,2018-11-19 23:59:59,watson,,21532.0
    2018-11-19 00:00:00,2018-11-19 23:59:59,watson,features,4323.0
    2018-11-19 00:00:00,2018-11-19 23:59:59,watson,docs,17209.0
    2018-11-20 00:00:00,2018-11-20 23:59:59,watson,,10235.0
    2018-11-20 00:00:00,2018-11-20 23:59:59,watson,features,917.0
    2018-11-20 00:00:00,2018-11-20 23:59:59,watson,docs,5863.0
    2018-11-20 00:00:00,2018-11-20 23:59:59,watson,website,3455.0
    2018-11-21 00:00:00,2018-11-21 23:59:59,watson,,77.0
    2018-11-21 00:00:00,2018-11-21 23:59:59,watson,docs,77.0
    """
    delta = (to - from_).days
    lines = []

    for i in range(delta + 1):
        offset = datetime.timedelta(days=i)
        from_offset = from_ + offset
        output = ctx.invoke(report, current=current, from_=from_offset,
                            to=from_offset, projects=projects, tags=tags,
                            output_format=output_format,
                            pager=pager, aggregated=True,
                            include_partial_frames=True)

        if 'json' in output_format:
            lines.append(output)
        elif 'csv' in output_format:
            lines.extend(flatten_report_for_csv(output))
        else:
            # if there is no activity for the day, append a newline
            # this ensures even spacing throughout the report
            if (len(output)) == 1:
                output[0] += '\n'

            lines.append('\n'.join(output))

    if 'json' in output_format:
        click.echo(json.dumps(lines, indent=4, sort_keys=True,
                   default=json_arrow_encoder))
    elif 'csv' in output_format:
        click.echo(build_csv(lines))
    elif pager or (pager is None and
                   watson.config.getboolean('options', 'pager', True)):
        click.echo_via_pager('\n\n'.join(lines))
    else:
        click.echo('\n\n'.join(lines))


@cli.command()
@click.option('-c/-C', '--current/--no-current', 'current', default=None,
              help="(Don't) include currently running frame in output.")
@click.option('-r/-R', '--reverse/--no-reverse', 'reverse', default=None,
              help="(Don't) reverse the order of the days in output.")
@click.option('-f', '--from', 'from_', type=DateTime,
              default=arrow.now().shift(days=-7),
              help="The date from when the log should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', type=DateTime, default=arrow.now(),
              help="The date at which the log should stop (inclusive). "
              "Defaults to tomorrow.")
@click.option('-y', '--year', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['year'],
              mutually_exclusive=['day', 'week', 'month', 'all'],
              help='Reports activity for the current year.')
@click.option('-m', '--month', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['month'],
              mutually_exclusive=['day', 'week', 'year', 'all'],
              help='Reports activity for the current month.')
@click.option('-l', '--luna', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['luna'],
              mutually_exclusive=['day', 'week', 'month', 'year', 'all'],
              help='Reports activity for the current moon cycle.')
@click.option('-w', '--week', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['week'],
              mutually_exclusive=['day', 'month', 'year', 'all'],
              help='Reports activity for the current week.')
@click.option('-d', '--day', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['day'],
              mutually_exclusive=['week', 'month', 'year', 'all'],
              help='Reports activity for the current day.')
@click.option('-a', '--all', cls=MutuallyExclusiveOption, type=DateTime,
              flag_value=_SHORTCUT_OPTIONS_VALUES['all'],
              mutually_exclusive=['day', 'week', 'month', 'year'],
              help='Reports all activities.')
@click.option('-p', '--project', 'projects', shell_complete=get_projects,
              multiple=True,
              help="Logs activity only for the given project. You can add "
              "other projects by using this option several times.")
@click.option('-T', '--tag', 'tags', shell_complete=get_tags, multiple=True,
              help="Logs activity only for frames containing the given "
              "tag. You can add several tags by using this option multiple "
              "times")
@click.option('--ignore-project', 'ignore_projects', multiple=True,
              help="Logs activity for all projects but the given ones. You "
              "can ignore several projects by using the option multiple "
              "times. Any given project will be ignored")
@click.option('--ignore-tag', 'ignore_tags', multiple=True,
              help="Logs activity for all tags but the given ones. You can "
              "ignore several tags by using the option multiple times. Any "
              "given tag will be ignored")
@click.option('-j', '--json', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='json', mutually_exclusive=['csv'],
              help="Format output in JSON instead of plain text")
@click.option('-s', '--csv', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='csv', mutually_exclusive=['json'],
              help="Format output in CSV instead of plain text")
@click.option('--plain', 'output_format', cls=MutuallyExclusiveOption,
              flag_value='plain', mutually_exclusive=['json', 'csv'],
              default=True, hidden=True,
              help="Format output in plain text (default)")
@click.option('-g/-G', '--pager/--no-pager', 'pager', default=None,
              help="(Don't) view output through a pager.")
@click.pass_obj
@catch_watson_error
def log(watson, current, reverse, from_, to, projects, tags, ignore_projects,
        ignore_tags, year, month, week, day, luna, all, output_format, pager):
    """
    Display each recorded session during the given timespan.

    By default, the sessions from the last 7 days are printed. This timespan
    can be controlled with the `--from` and `--to` arguments. The dates
    must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

    You can also use special shortcut options for easier timespan control:
    `--day` sets the log timespan to the current day (beginning at `00:00h`)
    and `--year`, `--month` and `--week` to the current year, month, or week,
    respectively.
    The shortcut `--luna` sets the timespan to the current moon cycle with
    the last full moon marking the start of the cycle.

    If you are outputting to the terminal, you can selectively enable a pager
    through the `--pager` option.

    You can limit the log to a project or a tag using the `--project`,
    `--tag`, `--ignore-project` and `--ignore-tag` options. They can be
    specified several times each to add or ignore multiple projects or
    tags in the log.

    You can change the output format from *plain text* to *JSON* using the
    `--json` option or to *CSV* using the `--csv` option. Only one of these
    two options can be used at once.

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
    \b
    $ watson log --from 2014-04-16 --to 2014-04-17 --csv
    id,start,stop,project,tags
    a96fcde,2014-04-17 09:15,2014-04-17 09:43,hubble,"lens, camera, transmission"
    5e91316,2014-04-17 10:19,2014-04-17 12:59,hubble,"camera, transmission"
    761dd51,2014-04-17 14:42,2014-04-17 15:54,voyager1,antenna
    02cb269,2014-04-16 09:53,2014-04-16 12:43,apollo11,wheels
    1070ddb,2014-04-16 13:48,2014-04-16 16:17,voyager1,"antenna, sensors"
    """  # noqa
    for start_time in (_ for _ in [day, week, month, luna, year, all]
                       if _ is not None):
        from_ = start_time

    if from_ > to:
        raise click.ClickException("'from' must be anterior to 'to'")

    if bool(projects and ignore_projects and
            set(projects).intersection(set(ignore_projects))):
        raise click.ClickException(
            "given projects can't be ignored at the same time")

    if bool(tags and ignore_tags and set(tags).intersection(set(ignore_tags))):
        raise click.ClickException(
            "given tags can't be ignored at the same time")

    if watson.current:
        if current or (current is None and
                       watson.config.getboolean('options', 'log_current')):
            cur = watson.current
            watson.frames.add(cur['project'], cur['start'], arrow.utcnow(),
                              cur['tags'], id="current")

    if reverse is None:
        reverse = watson.config.getboolean('options', 'reverse_log', True)

    day_start_hour = watson.config.getint('options', 'day_start_hour', 0)
    span = watson.frames.span(from_, to, day_start_hour)
    filtered_frames = watson.frames.filter(
        projects=projects or None, tags=tags or None,
        ignore_projects=ignore_projects or None,
        ignore_tags=ignore_tags or None, span=span
    )

    if 'json' in output_format:
        click.echo(frames_to_json(filtered_frames))
        return

    if 'csv' in output_format:
        click.echo(frames_to_csv(filtered_frames))
        return

    frames_by_day = sorted_groupby(
        filtered_frames,
        operator.attrgetter('day'),
        reverse=reverse
    )

    lines = []
    # use the pager, or print directly to the terminal
    if pager or (pager is None and
                 watson.config.getboolean('options', 'pager', True)):

        def _print(line):
            lines.append(line)

        def _final_print(lines):
            click.echo_via_pager('\n'.join(lines))
    else:

        def _print(line):
            click.echo(line)

        def _final_print(lines):
            pass

    for i, (day, frames) in enumerate(frames_by_day):
        if i != 0:
            _print('')

        frames = sorted(frames, key=operator.attrgetter('start'))
        longest_project = max(len(frame.project) for frame in frames)

        daily_total = reduce(
            operator.add,
            (frame.stop - frame.start for frame in frames)
        )

        _print(
            "{date} ({daily_total})".format(
                date=style('date', "{:dddd DD MMMM YYYY}".format(day)),
                daily_total=style('time', format_timedelta(daily_total))
            )
        )

        _print("\n".join(
            "\t{id}  {start} to {stop}  {delta:>11}  {project}{tags}".format(
                delta=format_timedelta(frame.stop - frame.start),
                project=style('project', '{:>{}}'.format(
                    frame.project, longest_project
                )),
                tags=(" "*2 if frame.tags else "") + style('tags', frame.tags),
                start=style('time', '{:HH:mm}'.format(frame.start)),
                stop=style('time', '{:HH:mm}'.format(frame.stop)),
                id=style('short_id', frame.id)
            )
            for frame in frames
        ))

    _final_print(lines)


@cli.command()
@click.pass_obj
@catch_watson_error
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
@catch_watson_error
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
@catch_watson_error
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
@click.argument('args', nargs=-1,
                shell_complete=get_project_or_task_completion)
@click.option('-f', '--from', 'from_', required=True, type=DateTime,
              help="Date and time of start of tracked activity")
@click.option('-t', '--to', required=True, type=DateTime,
              help="Date and time of end of tracked activity")
@click.option('-c', '--confirm-new-project', is_flag=True, default=False,
              help="Confirm addition of new project.")
@click.option('-b', '--confirm-new-tag', is_flag=True, default=False,
              help="Confirm creation of new tag.")
@click.pass_obj
@catch_watson_error
def add(watson, args, from_, to, confirm_new_project, confirm_new_tag):
    """
    Add time to a project with tag(s) that was not tracked live.

    Example:

    \b
    $ watson add --from "2018-03-20 12:00:00" --to "2018-03-20 13:00:00" \\
     programming +addfeature
    """
    # parse project name from args
    project = ' '.join(
        itertools.takewhile(lambda s: not s.startswith('+'), args)
    )
    if not project:
        raise click.ClickException("No project given.")

    # Confirm creation of new project if that option is set
    if (watson.config.getboolean('options', 'confirm_new_project') or
            confirm_new_project):
        confirm_project(project, watson.projects)

    # Parse all the tags
    tags = parse_tags(args)

    # Confirm creation of new tag(s) if that option is set
    if (watson.config.getboolean('options', 'confirm_new_tag') or
            confirm_new_tag):
        confirm_tags(tags, watson.tags)

    # add a new frame, call watson save to update state files
    frame = watson.add(project=project, tags=tags, from_date=from_, to_date=to)
    click.echo(
        "Adding project {}{}, started {} and stopped {}. (id: {})".format(
            style('project', frame.project),
            (" " if frame.tags else "") + style('tags', frame.tags),
            style('time', frame.start.humanize()),
            style('time', frame.stop.humanize()),
            style('short_id', frame.id)
        )
    )
    watson.save()


@cli.command(context_settings={'ignore_unknown_options': True})
@click.option('-c', '--confirm-new-project', is_flag=True, default=False,
              help="Confirm addition of new project.")
@click.option('-b', '--confirm-new-tag', is_flag=True, default=False,
              help="Confirm creation of new tag.")
@click.argument('id', required=False, shell_complete=get_frames)
@click.pass_obj
@catch_watson_error
def edit(watson, confirm_new_project, confirm_new_tag, id):
    """
    Edit a frame.

    You can specify the frame to edit by its position or by its frame id.
    For example, to edit the second-to-last frame, pass `-2` as the frame
    index. You can get the id of a frame with the `watson log` command.

    If no id or index is given, the frame defaults to the current frame (or the
    last recorded frame, if no project is currently running).

    The editor used is determined by the `VISUAL` or `EDITOR` environment
    variables (in that order) and defaults to `notepad` on Windows systems and
    to `vim`, `nano`, or `vi` (first one found) on all other systems.
    """
    date_format = 'YYYY-MM-DD'
    time_format = 'HH:mm:ss'
    datetime_format = '{} {}'.format(date_format, time_format)
    local_tz = local_tz_info()

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

    start = None
    stop = None

    # enter into while loop until successful and validated
    #  edit has been performed
    while True:
        output = click.edit(text, extension='.json')

        if not output:
            click.echo("No change made.")
            return

        try:
            data = json.loads(output)
            project = data['project']
            # Confirm creation of new project if that option is set
            if (watson.config.getboolean('options', 'confirm_new_project') or
                    confirm_new_project):
                confirm_project(project, watson.projects)
            tags = data['tags']
            # Confirm creation of new tag(s) if that option is set
            if (watson.config.getboolean('options', 'confirm_new_tag') or
                    confirm_new_tag):
                confirm_tags(tags, watson.tags)
            start = arrow.get(data['start'], datetime_format).replace(
                tzinfo=local_tz).to('utc')
            stop = arrow.get(data['stop'], datetime_format).replace(
                tzinfo=local_tz).to('utc') if id else None
            # if start time of the project is not before end time
            #  raise ValueException
            if not watson.is_started and start > stop:
                raise ValueError(
                    "Task cannot end before it starts.")
            if start > arrow.utcnow():
                raise ValueError("Start time cannot be in the future")
            if stop and stop > arrow.utcnow():
                raise ValueError("Stop time cannot be in the future")
            # break out of while loop and continue execution of
            #  the edit function normally
            break
        except (ValueError, TypeError, RuntimeError) as e:
            click.echo("Error while parsing inputted values: {}".format(e),
                       err=True)
        except KeyError:
            click.echo(
                "The edited frame must contain the project, "
                "start, and stop keys.", err=True)
        # we reach here if exception was thrown, wait for user
        #  to acknowledge the error before looping in while and
        #  showing user the editor again
        click.pause(err=True)
        # use previous entered values to the user in editor
        #  instead of original ones
        text = output

    # we reach this when we break out of the while loop above
    if id:
        watson.frames[id] = (project, start, stop, tags)
    else:
        watson.current = dict(start=start, project=project, tags=tags)

    watson.save()
    click.echo(
        "Edited frame for project {project}{tags}, from {start} to {stop} "
        "({delta})".format(
            delta=format_timedelta(stop - start) if stop else '-',
            project=style('project', project),
            tags=(" " if tags else "") + style('tags', tags),
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
@click.argument('id', shell_complete=get_frames)
@click.option('-f', '--force', is_flag=True,
              help="Don't ask for confirmation.")
@click.pass_obj
@catch_watson_error
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
            "{project}{tags} from {start} to {stop}, continue?".format(
                project=style('project', frame.project),
                tags=(" " if frame.tags else "") + style('tags', frame.tags),
                start=style('time', '{:HH:mm}'.format(frame.start)),
                stop=style('time', '{:HH:mm}'.format(frame.stop))
            ),
            abort=True
        )

    del watson.frames[id]

    watson.save()
    click.echo("Frame removed.")


@cli.command()
@click.argument('key', required=False, metavar='SECTION.OPTION')
@click.argument('value', required=False)
@click.option('-e', '--edit', is_flag=True,
              help="Edit the configuration file with an editor.")
@click.pass_context
@catch_watson_error
def config(context, key, value, edit):
    """
    Get and set configuration options.

    If `value` is not provided, the content of the `key` is displayed. Else,
    the given `value` is set.

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
            raise click.ClickException(style('error', str(exc)))
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
@catch_watson_error
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
@catch_watson_error
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
@click.argument('rename_type', required=True, metavar='TYPE',
                shell_complete=get_rename_types)
@click.argument('old_name', required=True, shell_complete=get_rename_name)
@click.argument('new_name', required=True, shell_complete=get_rename_name)
@click.pass_obj
@catch_watson_error
def rename(watson, rename_type, old_name, new_name):
    """
    Rename a project or tag.

    Example:

    \b
    $ watson rename project read-python-intro learn-python
    Renamed project "read-python-intro" to "learn-python"
    $ watson rename tag company-meeting meeting
    Renamed tag "company-meeting" to "meeting"

    """
    if rename_type == 'tag':
        watson.rename_tag(old_name, new_name)
        click.echo('Renamed tag "{}" to "{}"'.format(
                        style('tag', old_name),
                        style('tag', new_name)
                   ))
    elif rename_type == 'project':
        watson.rename_project(old_name, new_name)
        click.echo('Renamed project "{}" to "{}"'.format(
                        style('project', old_name),
                        style('project', new_name)
                   ))
    else:
        raise click.ClickException(style(
            'error',
            'You have to call rename with type "project" or "tag"; '
            'you supplied "%s"' % rename_type
        ))
