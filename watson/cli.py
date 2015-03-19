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

        return '[{}]'.format(', '.join(
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
    Start monitoring the time for the given project. You can add tags
    indicating more specifically what you are working on with '+tag'.

    \b
    Example :
    $ watson start apollo11 +module +brakes
    Starting apollo11 [module, brakes] at 16:34
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
    click.echo("Starting {} {} at {}".format(
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
    click.echo("Stopping project {} {}, started {}.".format(
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
    click.echo("Canceling the timer for project {} {}".format(
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
    click.echo("Project {} {} started {}".format(
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
    14h 51m 35s apollo11
            [14h 49m 46s brakes]
            [ 8h 58m 20s module]
            [10h 01m 20s reactor]
            [12h 39m 40s steering]
            [11h 34m 51s wheels]
    11h 34m 36s hubble
            [ 8h 07m 26s camera]
            [ 7h 59m 32s lens]
            [ 9h 20m 33s transmission]
     7h 47m 41s voyager1
            [ 1h 25m 32s antenna]
            [ 1h 25m 32s generators]
            [ 1h 25m 32s probe]
     9h 28m 28s voyager2
            [ 5h 31m 48s antenna]
            [ 9h 08m 25s generators]
            [ 2h 43m 03s probe]
            [ 5h 51m 51s sensors]

    \b
    Total: 43h 42m 20s

    \b
    $ watson log --from 2014-04-01 --to 2014-04-30  apollo11
    Tue 01 April 2014 -> Wed 30 April 2014

    \b
    39h 44m 06s apollo11
            [17h 49m 47s brakes]
            [10h 12m 06s module]
            [22h 44m 33s reactor]
            [14h 08m 04s steering]
            [11h 19m 01s wheels]
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
        frames = tuple(watson.frames.filter(projects=[name], span=span))
        delta = reduce(
            operator.add,
            (f.stop - f.start for f in frames),
            datetime.timedelta()
        )
        total += delta

        click.echo("{project} - {time}".format(
            time=style('time', format_timedelta(delta)),
            project=style('project', name)
        ))

        tags = sorted(set(tag for frame in frames for tag in frame.tags))
        longest_tag = max(len(tag) for tag in tags)

        for tag in tags:
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
              help="The date from when the report should start. Defaults "
              "to seven days ago.")
@click.option('-t', '--to', type=Date, default=arrow.now(),
              help="The date at which the report should stop (inclusive). "
              "Defaults to tomorrow.")
@click.option('-p', '--project', 'projects', multiple=True,
              help="Reports activity only for the given project. You can add "
              "other projects by using this option several times.")
@click.option('--tag', 'tags', multiple=True,
              help="Reports activity only for frames containing the given "
              "tag. You can add several tags by using this option multiple "
              "times")
@click.pass_obj
def report(watson, from_, to, projects, tags):
    """
    Print a report of the time spent on projects during the given timespan.

    By default, the time spent the last 7 days is printed. This timespan
    can be controlled with the '--from' and '--to' arguments. The dates
    must have the format 'YEAR-MONTH-DAY', like: '2014-05-19'.

    You can limit the report to a project or a tag using the `--project` and
    `--tag` options. They can be specified several times each to add multiple
    projects or tags to the report.

    \b
    Example:
    $ watson report --project voyager2 --project apollo11
    Monday 05 May 2014
            a7f8157  09:57 to 12:05  apollo11  2h 08m 34s
            44866f1  12:32 to 16:21  voyager2  3h 48m 59s
            4864459  16:36 to 19:12  voyager2 [antenna]  2h 35m 07s

    \b
    Tuesday 06 May 2014
            3142104  09:49 to 12:49  voyager2 [sensors]  2h 59m 20s
            8c99d9e  13:03 to 14:43  voyager2 [antenna, sensors]  1h 39m 45s
            0469b72  15:41 to 18:40  voyager2 [antenna, probe]  2h 59m 03s

    \b
    Wednesday 07 May 2014
            0d2be24  09:16 to 10:53  apollo11 [reactor, steering]  1h 36m 53s
            0ae6308  11:41 to 14:21  apollo11 [wheels, brakes]  2h 39m 53s

    \b
    Thursday 08 May 2014
            b4f3d47  09:34 to 11:29  voyager2 [generators, probe]  1h 55m 01s
            7c31426  17:30 to 18:39  voyager2 [sensors, probe]  1h 08m 59s


    \b
    $ watson report --from 2014-04-16 --to 2014-04-17
    Wednesday 16 April 2014
            c983586  09:28 to 12:55  apollo11  3h 26m 12s
            1a5dbe5  13:52 to 14:51  voyager2 [sensors, antenna] 58m 21s
            478ad13  15:44 to 16:52  hubble [transmission]  1h 07m 43s

    \b
    Thursday 17 April 2014
            a57e276  09:29 to 12:33  voyager1 [antenna, probe]  3h 04m 45s
            8f25306  13:03 to 13:15  voyager1 11m 53s
            975c6f6  13:46 to 17:34  apollo11 [reactor]  3h 47m 29s
    """
    if from_ > to:
        raise click.ClickException("'from' must be anterior to 'to'")

    span = watson.frames.span(from_, to)
    frames_by_day = itertools.groupby(
        watson.frames.filter(
            projects=projects or None, tags=tags or None, span=span
        ),
        operator.attrgetter('day')
    )

    for i, (day, frames) in enumerate(frames_by_day):
        if i != 0:
            click.echo()

        frames = tuple(frames)
        longest_project = max(len(frame.project) for frame in frames)

        click.echo(style('date', "{:dddd DD MMMM YYYY}".format(day)))

        click.echo('\n'.join(
            '\t{id}  {start} to {stop}  {delta:>10}  {project}  {tags}'.format(
                delta=format_timedelta(frame.stop - frame.start),
                project=style('project',
                              '{:>{}}'.format(frame.project, longest_project)),
                pad=longest_project,
                tags=style('tags', frame.tags),
                start=style('time',
                            '{:HH:mm}'.format(frame.start.to('local'))),
                stop=style('time',
                           '{:HH:mm}'.format(frame.stop.to('local'))),
                id=style('id', frame.id[:7])
            )
            for frame in frames
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
        'Edited frame for project {project} {tags}, from {start} to {stop} '
        '({delta})'.format(
            delta=format_timedelta(frame.stop - frame.start),
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
