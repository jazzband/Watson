import datetime
import itertools
import json
import os
import shutil
import tempfile

import click
import arrow

from click.exceptions import UsageError


try:
    text_type = (str, unicode)
except NameError:
    text_type = str


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
        start_time = arrow.Arrow.fromdate(now.replace(days=-weekday).date())
    elif period == 'month':
        start_time = arrow.Arrow(year, month, 1)
    elif period == 'year':
        start_time = arrow.Arrow(year, 1, 1)
    else:
        raise ValueError('Unsupported period value: {}'.format(period))

    return start_time


def make_json_writer(func, *args, **kwargs):
    """
    Return a function that receives a file-like object and writes the return
    value of func(*args, **kwargs) as JSON to it.
    """
    def writer(f):
        json.dump(func(*args, **kwargs), f, indent=1, ensure_ascii=False)
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
            if isinstance(content, text_type):
                tmpfp.write(content)
            else:
                content(tmpfp)
    except:
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
