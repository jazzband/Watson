import uuid

import arrow

from collections import namedtuple

HEADERS = ('start', 'stop', 'project', 'id', 'tags', 'updated_at')


class Frame(namedtuple('Frame', HEADERS)):
    def __new__(cls, start, stop, project, id, tags=None, updated_at=None,):
        try:
            if not isinstance(start, arrow.Arrow):
                start = arrow.get(start)

            if not isinstance(stop, arrow.Arrow):
                stop = arrow.get(stop)
        except RuntimeError as e:
            from .watson import WatsonError
            raise WatsonError("Error converting date: {}".format(e))

        start = start.to('local')
        stop = stop.to('local')

        if updated_at is None:
            updated_at = arrow.utcnow()
        elif not isinstance(updated_at, arrow.Arrow):
            updated_at = arrow.get(updated_at)

        if tags is None:
            tags = []

        return super(Frame, cls).__new__(
            cls, start, stop, project, id, tags, updated_at
        )

    def dump(self):
        start = self.start.to('utc').timestamp
        stop = self.stop.to('utc').timestamp
        updated_at = self.updated_at.timestamp

        return (start, stop, self.project, self.id, self.tags, updated_at)

    @property
    def day(self):
        return self.start.floor('day')

    def __lt__(self, other):
        return self.start < other.start

    def __lte__(self, other):
        return self.start <= other.start

    def __gt__(self, other):
        return self.start > other.start

    def __gte__(self, other):
        return self.start >= other.start


class Span(object):
    def __init__(self, start, stop, timeframe='day'):
        self.timeframe = timeframe
        self.start = start.floor(self.timeframe)
        self.stop = stop.ceil(self.timeframe)

    def __contains__(self, frame):
        return frame.start >= self.start and frame.stop <= self.stop


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
            return tuple(self._get_col(key))
        elif isinstance(key, int):
            return self._rows[key]
        else:
            return self._rows[self._get_index_by_id(key)]

    def __setitem__(self, key, value):
        self.changed = True

        if isinstance(value, Frame):
            frame = value
        else:
            frame = self.new_frame(*value)

        if isinstance(key, int):
            self._rows[key] = frame
        else:
            frame = frame._replace(id=key)
            try:
                self._rows[self._get_index_by_id(key)] = frame
            except KeyError:
                self._rows.append(frame)

    def __delitem__(self, key):
        self.changed = True

        if isinstance(key, int):
            del self._rows[key]
        else:
            del self._rows[self._get_index_by_id(key)]

    def _get_index_by_id(self, id):
        try:
            return next(
                i for i, v in enumerate(self['id']) if v.startswith(id)
            )
        except StopIteration:
            raise KeyError("Frame with id {} not found.".format(id))

    def _get_col(self, col):
        index = HEADERS.index(col)
        for row in self._rows:
            yield row[index]

    def add(self, *args, **kwargs):
        self.changed = True
        frame = self.new_frame(*args, **kwargs)
        self._rows.append(frame)
        return frame

    def new_frame(self, project, start, stop, tags=None, id=None,
                  updated_at=None):
        if not id:
            id = uuid.uuid4().hex
        return Frame(start, stop, project, id, tags=tags,
                     updated_at=updated_at)

    def dump(self):
        return tuple(frame.dump() for frame in self._rows)

    def filter(self, projects=None, tags=None, span=None):
        return (
            frame for frame in self._rows
            if (projects is None or frame.project in projects) and
               (tags is None or any(tag in frame.tags for tag in tags)) and
               (span is None or frame in span)
        )

    def span(self, start, stop):
        return Span(start, stop)
