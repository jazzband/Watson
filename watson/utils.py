import collections as co
import csv
import datetime
import itertools
import json
import operator
import os
import shutil
import tempfile
from io import StringIO
import click
import arrow

import watson as _watson
from .fullmoon import get_last_full_moon

from click.exceptions import UsageError


def create_watson():
    return _watson.Watson(config_dir=os.environ.get('WATSON_DIR'))


def confirm_project(project, watson_projects):
    """
    Ask user to confirm creation of a new project
    'project' must be a string
    'watson_projects' must be an interable.
    Returns True on accept and raises click.exceptions.Abort on reject
    """
    if project not in watson_projects:
        msg = ("Project '%s' does not exist yet. Create it?"
               % style('project', project))
        click.confirm(msg, abort=True)
    return True


def confirm_tags(tags, watson_tags):
    """
    Ask user to confirm creation of new tags (each separately)
    Both 'tags' and 'watson_tags" must be iterables.
    Returns True if all accepted and raises click.exceptions.Abort on reject
    """
    for tag in tags:
        if tag not in watson_tags:
            msg = "Tag '%s' does not exist yet. Create it?" % style('tag', tag)
            click.confirm(msg, abort=True)
    return True


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


def format_timedelta(delta):
    """
    Return a string roughly representing a timedelta.
    """
    seconds = int(delta.total_seconds())
    neg = seconds < 0
    seconds = abs(seconds)
    total = seconds
    stems = []

    if total >= 3600:
        hours = seconds // 3600
        stems.append('{}h'.format(hours))
        seconds -= hours * 3600

    if total >= 60:
        mins = seconds // 60
        stems.append('{:02}m'.format(mins))
        seconds -= mins * 60

    stems.append('{:02}s'.format(seconds))

    return ('-' if neg else '') + ' '.join(stems)


def sorted_groupby(iterator, key, reverse=False):
    """
    Similar to `itertools.groupby`, but sorts the iterator with the same
    key first.
    """
    return itertools.groupby(sorted(iterator, key=key, reverse=reverse), key)


def options(opt_list):
    """
    Wrapper for the `value_proc` field in `click.prompt`, which validates
    that the user response is part of the list of accepted responses.
    """
    def value_proc(user_input):
        if user_input in opt_list:
            return user_input
        else:
            raise UsageError("Response should be one of [{}]".format(
                ','.join(str(x) for x in opt_list)))
    return value_proc


def get_frame_from_argument(watson, arg):
    """
    Get a frame from a command line argument which can either be a
    position index (-1) or a frame id.
    """
    # first we try to see if we are refering to a frame by
    # its position (for example -2). We only take negative indexes
    # as a positive index might also be an existing id
    try:
        index = int(arg)
        if index < 0:
            return watson.frames[index]
    except IndexError:
        raise click.ClickException(
            style('error', "No frame found for index {}.".format(arg))
        )
    except (ValueError, TypeError):
        pass

    # if we didn't find a frame by position, we try by id
    try:
        return watson.frames[arg]
    except KeyError:
        raise click.ClickException("{} {}.".format(
            style('error', "No frame found with id"),
            style('short_id', arg))
        )


def get_start_time_for_period(period):
    # Using now() from datetime instead of arrow for mocking compatibility.
    now = arrow.Arrow.fromdatetime(datetime.datetime.now())
    date = now.date()

    day = date.day
    month = date.month
    year = date.year

    weekday = now.weekday()

    if period == 'day':
        start_time = arrow.Arrow(year, month, day)
    elif period == 'week':
        start_time = arrow.Arrow.fromdate(now.shift(days=-weekday).date())
    elif period == 'month':
        start_time = arrow.Arrow(year, month, 1)
    elif period == 'luna':
        start_time = get_last_full_moon(now)
    elif period == 'year':
        start_time = arrow.Arrow(year, 1, 1)
    elif period == 'all':
        # approximately timestamp `0`
        start_time = arrow.Arrow(1970, 1, 1)
    else:
        raise ValueError('Unsupported period value: {}'.format(period))

    return start_time


def apply_weekday_offset(start_time, week_start):
    """
    Apply the offset required to move the start date `start_time` of a week
    starting on Monday to that of a week starting on `week_start`.
    """
    weekdays = dict(zip(
        ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
         "sunday"], range(0, 7)))

    new_start = week_start.lower()
    if new_start not in weekdays:
        return start_time
    now = datetime.datetime.now()
    offset = weekdays[new_start] - 7 * (weekdays[new_start] > now.weekday())
    return start_time.shift(days=offset)


def make_json_writer(func, *args, **kwargs):
    """
    Return a function that receives a file-like object and writes the return
    value of func(*args, **kwargs) as JSON to it.
    """
    def writer(f):
        dump = json.dumps(func(*args, **kwargs), indent=1, ensure_ascii=False)
        f.write(dump)
    return writer


def safe_save(path, content, ext='.bak'):
    """
    Save given content to file at given path safely.

    `content` may either be a (unicode) string to write to the file, or a
    function taking one argument, a file object opened for writing. The
    function may write (unicode) strings to the file object (but doesn't need
    to close it).

    The file to write to is created at a temporary location first. If there is
    an error creating or writing to the temp file or calling `content`, the
    destination file is left untouched. Otherwise, if all is well, an existing
    destination file is backed up to `path` + `ext` (defaults to '.bak') and
    the temporary file moved into its place.

    """
    tmpfp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    try:
        with tmpfp:
            if isinstance(content, str):
                tmpfp.write(content)
            else:
                content(tmpfp)
    except Exception:
        try:
            os.unlink(tmpfp.name)
        except (IOError, OSError):
            pass
        raise
    else:
        if os.path.exists(path):
            try:
                os.unlink(path + ext)
            except OSError:
                pass
            shutil.move(path, path + ext)

        shutil.move(tmpfp.name, path)


def deduplicate(sequence):
    """
    Return a list with all items of the input sequence but duplicates removed.

    Leaves the input sequence unaltered.
    """
    return [element
            for index, element in enumerate(sequence)
            if element not in sequence[:index]]


def parse_tags(values_list):
    """
    Return a list of tags parsed from the input values list.

    Find all the tags starting by a '+', even if there are spaces in them,
    then strip each tag and filter out the empty ones
    """
    return list(filter(None, map(operator.methodcaller('strip'), (
        # We concatenate the word with the '+' to the following words
        # not starting with a '+'
        w[1:] + ' ' + ' '.join(itertools.takewhile(
            lambda s: not s.startswith('+'), values_list[i + 1:]
        ))
        for i, w in enumerate(values_list) if w.startswith('+')
    ))))  # pile of pancakes !


def frames_to_json(frames):
    """
    Transform a sequence of frames into a JSON-formatted string.

    Each frame object has an equivalent pair name/value in the JSON string,
    except for 'updated_at', which is not included.

    .. seealso:: :class:`Frame`
    """
    log = [
        co.OrderedDict([
            ('id', frame.id),
            ('start', frame.start.isoformat()),
            ('stop', frame.stop.isoformat()),
            ('project', frame.project),
            ('tags', frame.tags),
        ])
        for frame in frames
    ]
    return json.dumps(log, indent=4, sort_keys=True)


def frames_to_csv(frames):
    """
    Transform a sequence of frames into a CSV-formatted string.

    Each frame object has an equivalent pair name/value in the CSV string,
    except for 'updated_at', which is not included.

    .. seealso:: :class:`Frame`
    """
    entries = [
        co.OrderedDict([
            ('id', frame.id[:7]),
            ('start', frame.start.format('YYYY-MM-DD HH:mm:ss')),
            ('stop', frame.stop.format('YYYY-MM-DD HH:mm:ss')),
            ('project', frame.project),
            ('tags', ', '.join(frame.tags)),
        ])
        for frame in frames
    ]
    return build_csv(entries)


def build_csv(entries):
    """
    Creates a CSV string from a list of dict objects.

    The dictionary keys of the first item in the list are used as the header
    row for the built CSV. All item's keys are supposed to be identical.
    """
    if entries:
        header = entries[0].keys()
    else:
        return ''
    memfile = StringIO()
    writer = csv.DictWriter(memfile, header, lineterminator=os.linesep)
    writer.writeheader()
    writer.writerows(entries)
    output = memfile.getvalue()
    memfile.close()
    return output


def flatten_report_for_csv(report):
    """
    Flattens the data structure returned by `watson.report()` for a csv export.

    Dates are formatted in a way that Excel (default csv module dialect) can
    handle them (i.e. YYYY-MM-DD HH:mm:ss).

    The result is a list of dictionaries where each element can contain two
    different things:

    1. The total `time` spent in a project during the report interval. In this
       case, the `tag` value will be empty.
    2. The partial `time` spent in a tag and project during the report
       interval. In this case, the `tag` value will contain a tag associated
       with the project.

    The sum of all elements where `tag` is empty corresponds to the total time
    of the report.
    """
    result = []
    datetime_from = report['timespan']['from'].format('YYYY-MM-DD HH:mm:ss')
    datetime_to = report['timespan']['to'].format('YYYY-MM-DD HH:mm:ss')
    for project in report['projects']:
        result.append({
            'from': datetime_from,
            'to': datetime_to,
            'project': project['name'],
            'tag': '',
            'time': project['time']
        })
        for tag in project['tags']:
            result.append({
                'from': datetime_from,
                'to': datetime_to,
                'project': project['name'],
                'tag': tag['name'],
                'time': tag['time']
            })
    return result


def json_arrow_encoder(obj):
    """
    Encodes Arrow objects for JSON output.
    This function can be used with
    `json.dumps(..., default=json_arrow_encoder)`, for example.
    If the object is not an Arrow type, a TypeError is raised
    :param obj: Object to encode
    :return: JSON representation of Arrow object as defined by Arrow
    """
    if isinstance(obj, arrow.Arrow):
        return obj.for_json()

    raise TypeError("Object {} is not JSON serializable".format(obj))
