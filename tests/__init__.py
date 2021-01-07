"""Utility functions for the unit tests."""

import os
import datetime
import mock
from io import StringIO

import py


TEST_FIXTURE_DIR = py.path.local(
    os.path.dirname(
        os.path.realpath(__file__)
        )
    ) / 'resources'


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
