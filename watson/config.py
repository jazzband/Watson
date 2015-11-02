# -*- coding: utf-8 -*-
"""A convenience and compatibility wrapper for RawConfigParser."""

try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

__all__ = ('ConfigParser',)


class ConfigParser(RawConfigParser):
    """A simple wrapper for RawConfigParser to make options access easier."""

    def get(self, section, option, default=None, **kwargs):
        """
        Return value of option in given configuration section as a string.

        If option is not set, return default instead (defaults to None).

        """
        return (RawConfigParser.get(self, section, option, **kwargs)
                if self.has_option(section, option) else default)

    def getint(self, section, option, default=None):
        """
        Return value of option in given configuration section as an integer.

        If option is not set, return default (defaults to None).

        Raises ValueError if the value cannot be converted to an integer.

        """
        val = self.get(section, option)
        return default if val is None else int(val)

    def getfloat(self, section, option, default=None):
        """
        Return value of option in given configuration section as a float.

        If option is not set, return default (defaults to None).

        Raises ValueError if the value cannot be converted to a float.

        """
        val = self.get(section, option)
        return default if val is None else float(val)

    def getboolean(self, section, option, default=False):
        """
        Return value of option in given configuration section as a boolean.

        A configuration option is considered true when it has one of the
        following values: '1', 'on', 'true' or 'yes'. The comparison is
        case-insensitive. All other values are considered false.

        If option is not set or empty, return default (defaults to False).

        """
        val = self.get(section, option)
        return val.lower() in ('1', 'on', 'true', 'yes') if val else default

    def set(self, section, option, value):
        """
        Set option in given configuration section to value.

        If section does not exist yet, it is added implicitly.

        """
        if not self.has_section(section):
            self.add_section(section)

        RawConfigParser.set(self, section, option, value)
