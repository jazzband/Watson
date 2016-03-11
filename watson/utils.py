import click
import datetime
import itertools

from click.exceptions import UsageError


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


def format_timedelta(delta, round_up_to=1):
    """
    Return a string roughly representing a timedelta. Round up to `round_up_to`
    minutes. No rounding by default.

    For reference, str(timedelta) returns [x days,] hh:mm:ss
    """
    neg = '-' if int(delta.total_seconds()) < 0 else ''
    delta = round_time(delta, round_up_to)
    fmt = ["{}h ", "{}m", " {}s"]
    td = str(abs(delta)).split(":")
    td[:0] = td.pop(0).split(',')
    if len(td) == 4:
        add_hours = int(td.pop(0).split()[0].strip()) * 24
        td[0] = str(int(td[0]) + add_hours)
    if round_up_to > 0:
        # Remove seconds when rounding
        del fmt[-1]
        del td[-1]
    res = str()
    for f, k in zip(fmt, td):
        res += f.format(k.strip())
    return "{}{}".format(neg, res)


def round_time(dt, round_up_to=1):
    """
    Round a datetime object _up_ to nearest round_to minutes.

    First round seconds up or down to the nearest minute, then round that
    result up to the nearest round_to minute.

    Set round_up_to=0 for no rounding

    """
    if round_up_to == 0:
        return dt
    round_dt = datetime.timedelta(minutes=round_up_to).total_seconds()
    seconds = int(dt.total_seconds())
    rounding = (seconds + 60 / 2) // 60 * 60
    dt += datetime.timedelta(0, rounding - seconds)
    seconds = int(dt.total_seconds())
    rounding = (seconds + round_dt) // round_dt * round_dt
    if dt.total_seconds() % (round_up_to * 60) != 0:
        return dt + datetime.timedelta(0, rounding - seconds)
    else:
        return dt


def sorted_groupby(iterator, key, reverse=False):
    """
    Similar to `itertools.groupby`, but sorts the iterator with the same
    key first.
    """
    return itertools.groupby(sorted(iterator, key=key, reverse=reverse), key)


def total_by_day(frames, round_to=0, tag=None, total=True):
    """
    Given an iterator of Frame objects, return a total result where the time
    for each day is summed and then rounded up to round_to. The rounded totals
    for each day (and for a tag if given) are then summed without rounding and
    returned as the result.
    """
    if tag == "<untagged>":
        frames = list((i for i in frames if not i.tags))
    else:
        frames = list((i for i in frames if not tag or tag in i.tags))
    days = [list(group) for k, group in
            sorted_groupby(frames,
                           key=lambda x: x.start.datetime.toordinal())]
    delta = []
    for day in days:
        day_iter = (f.stop - f.start for f in day)
        delta.append(round_time(sum(day_iter, datetime.timedelta()),
                                round_to))
    if total is True:
        return sum(delta, datetime.timedelta())
    else:
        return delta


def total_by_each_day(frames, round_to=0, tags=None):
    """
    Given an iterator of Frame objects, return a list of
    [(date, total), (...,.)] where the total for each day is summed (only for
    'tags' if given) and then rounded up to round_to.
    """
    frames = list(i for i in frames if not tags or
                  (set(i.tags).intersection(set(tags))
                   or "<untagged>" in tags))
    days = [list(group) for k, group in
            sorted_groupby(frames,
                           key=lambda x: x.start.datetime.toordinal())]
    delta = []
    for day in days:
        day_iter = (f.stop - f.start for f in day)
        delta.append((day[0].start, round_time(sum(day_iter,
                                                   datetime.timedelta()),
                                               round_to)))
    return delta


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
