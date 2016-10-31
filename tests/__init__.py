"""Utility functions for the unit tests."""

import datetime

try:
    from unittest import mock
except ImportError:
    import mock

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def mock_datetime(dt, dt_module):

    class DateTimeMeta(type):

        @classmethod
        def __instancecheck__(mcs, obj):
            return isinstance(obj, datetime.datetime)

    class BaseMockedDateTime(datetime.datetime):

        @classmethod
        def now(cls, tz=None):
            return dt.replace(tzinfo=tz)

        @classmethod
        def utcnow(cls):
            return dt

        @classmethod
        def today(cls):
            return dt

    MockedDateTime = DateTimeMeta('datetime', (BaseMockedDateTime,), {})

    return mock.patch.object(dt_module, 'datetime', MockedDateTime)


def mock_read(content):
    return lambda self, name: self._read(StringIO(content), name)
