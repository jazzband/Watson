# -*- coding: utf-8 -*-

import uuid

import arrow

from collections import OrderedDict, namedtuple

FIELDS = ('id', 'project', 'start', 'stop', 'tags', 'updated_at', 'message')


class Frame(namedtuple('Frame', FIELDS)):
    def __new__(cls, id, project, start, stop, tags=None, updated_at=None,
                message=None):
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
            cls, id, project, start, stop, tags, updated_at, message
        )

    def dump(self):
        start = self.start.to('utc').timestamp
        stop = self.stop.to('utc').timestamp
        updated_at = self.updated_at.timestamp

        return (self.id, self.project, start, stop, self.tags, updated_at,
                self.message)

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


class Frames(OrderedDict):
    def __init__(self, frames=None):
        super(Frames, self).__init__()
        self._keys = list(self.keys())

        for frame in frames or []:
            # convert from old format with project @ idx 2 and ID @ idx 3
            if not isinstance(frame[2], (int, float)):
                frame = (
                    frame[3],  # id
                    frame[2],  # project
                    frame[0],  # start
                    frame[1]   # stop
                ) + tuple(frame[4:])

            frame = Frame(*frame)
            self[frame.id] = frame

        self.changed = False

    def __getitem__(self, id):
        try:
            return super(Frames, self).__getitem__(id)
        except KeyError:
            for key in reversed(self._keys):
                if key.startswith(id):
                    return super(Frames, self).__getitem__(key)
            else:
                raise KeyError("Frame with id {} not found.".format(id))

    def __setitem__(self, key, value):
        if isinstance(value, Frame):
            frame = self.new_frame(value.project, value.start, value.stop,
                                   value.tags, value.updated_at, value.message,
                                   id=key)
        else:
            frame = self.new_frame(*value[:6], id=key)

        if key not in self:
            self._keys.append(key)

        super(Frames, self).__setitem__(key, frame)
        self.changed = True

    def __delitem__(self, key):
        super(Frames, self).__delitem__(key)
        self._keys.remove(key)
        self.changed = True

    def move_to_end(self, key, last=True):
        super(Frames, self).move_to_end(key, last)
        self._keys.remove(key)
        self._keys.insert(len(self._keys) if last else 0, key)

    def add(self, *args, **kwargs):
        frame = self.new_frame(*args, **kwargs)
        self[frame.id] = frame
        return frame

    def new_frame(self, project, start, stop, tags=None, updated_at=None,
                  message=None, id=None):
        if id is None:
            id = uuid.uuid4().hex

        return Frame(id, project, start, stop, tags, updated_at, message)

    def dump(self):
        return tuple(frame.dump() for frame in self.values())

    def filter(self, projects=None, tags=None, span=None):
        for frame in self.values():
            if ((projects is None or frame.project in projects) and
                    (tags is None or set(frame.tags).intersection(tags)) and
                    (span is None or frame in span)):
                yield frame

    def get_by_index(self, index):
        return self[self._keys[index]]

    def get_column(self, col):
        index = FIELDS.index(col)
        for row in self.values():
            yield row[index]

    def span(self, start, stop):
        return Span(start, stop)
