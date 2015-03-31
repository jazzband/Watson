import itertools


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
