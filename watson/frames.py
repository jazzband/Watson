import arrow

from collections import namedtuple

HEADERS = ('start', 'stop', 'project', 'id')


class Frame(namedtuple('Frame', HEADERS)):
    def __new__(cls, start, stop, project, id):
        if not isinstance(start, arrow.Arrow):
            start = arrow.get(start)

        if not isinstance(stop, arrow.Arrow):
            stop = arrow.get(stop)

        return super(Frame, cls).__new__(cls, start, stop, project, id)

    def dump(self):
        start = self.start.timestamp
        stop = self.stop.timestamp

        return (start, stop, self.project, self.id)


class Frames(object):
    def __init__(self, frames=None):
        if not frames:
            frames = []

        rows = [Frame(*frame) for frame in frames]
        self._rows = rows

        self.changed = False

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, key):
        if key in HEADERS:
            return self._get_col(key)
        else:
            return self._rows[key]

    def __setitem__(self, key, value):
        self.changed = True
        if isinstance(value, Frame):
            self._rows[key] = value
        else:
            self._rows[key] = self.new_frame(*value)

    def __delitem__(self, key):
        self.changed = True
        del self._rows[key]

    def _get_col(self, col):
        index = HEADERS.index(col)
        for row in self._rows:
            yield row[index]

    @property
    def rows(self):
        for row in self._rows:
            yield row

    def add(self, *args, **kwargs):
        self.changed = True
        self._rows.append(self.new_frame(*args, **kwargs))

    def new_frame(self, project, start, stop, id=None):
        return Frame(start, stop, project, id)

    def replace(self, index, **kwargs):
        frame = self[index]
        self[index] = frame._replace(**kwargs)

    def dump(self):
        return tuple(frame.dump() for frame in self._rows)
