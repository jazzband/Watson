def format_timedelta(delta):
    """
    Return a string roughly representing a timedelta.
    """
    seconds = int(delta.total_seconds())
    neg = seconds < 0
    seconds = abs(seconds)
    stems = []

    if seconds > 3600:
        hours = seconds // 3600
        stems.append('{:2}h'.format(hours))
        seconds -= hours * 3600

    if seconds > 60:
        mins = seconds // 60
        stems.append('{:02}m'.format(mins))
        seconds -= mins * 60

    if seconds >= 0:
        stems.append('{:02}s'.format(seconds))

    return '{:>12}'.format(('-' if neg else '') + ' '.join(stems))
