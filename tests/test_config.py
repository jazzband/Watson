"""Unit tests for the 'config' module."""

import pytest

from watson.config import ConfigParser

from . import mock_read


def test_config_get(mock, watson):
    content = u"""
[backend]
url = foo
token =
    """
    mock.patch.object(ConfigParser, 'read', mock_read(content))
    config = watson.config
    assert config.get('backend', 'url') == 'foo'
    assert config.get('backend', 'token') == ''
    assert config.get('backend', 'foo') is None
    assert config.get('backend', 'foo', 'bar') == 'bar'
    assert config.get('option', 'spamm') is None
    assert config.get('option', 'spamm', 'eggs') == 'eggs'


def test_config_getboolean(mock, watson):
    content = u"""
[options]
flag1 = 1
flag2 = ON
flag3 = True
flag4 = yes
flag5 = false
flag6 =
    """
    mock.patch.object(ConfigParser, 'read', mock_read(content))
    config = watson.config
    assert config.getboolean('options', 'flag1') is True
    assert config.getboolean('options', 'flag1', False) is True
    assert config.getboolean('options', 'flag2') is True
    assert config.getboolean('options', 'flag3') is True
    assert config.getboolean('options', 'flag4') is True
    assert config.getboolean('options', 'flag5') is False
    assert config.getboolean('options', 'flag6') is False
    assert config.getboolean('options', 'flag6', True) is True
    assert config.getboolean('options', 'missing') is False
    assert config.getboolean('options', 'missing', True) is True


def test_config_getint(mock, watson):
    content = u"""
[options]
value1 = 42
value2 = spamm
value3 =
    """
    mock.patch.object(ConfigParser, 'read', mock_read(content))
    config = watson.config
    assert config.getint('options', 'value1') == 42
    assert config.getint('options', 'value1', 666) == 42
    assert config.getint('options', 'missing') is None
    assert config.getint('options', 'missing', 23) == 23
    # default is not converted!
    assert config.getint('options', 'missing', '42') == '42'
    assert config.getint('options', 'missing', 6.66) == 6.66

    with pytest.raises(ValueError):
        config.getint('options', 'value2')

    with pytest.raises(ValueError):
        config.getint('options', 'value3')


def test_config_getfloat(mock, watson):
    content = u"""
[options]
value1 = 3.14
value2 = 42
value3 = spamm
value4 =
    """

    mock.patch.object(ConfigParser, 'read', mock_read(content))
    config = watson.config
    assert config.getfloat('options', 'value1') == 3.14
    assert config.getfloat('options', 'value1', 6.66) == 3.14
    assert config.getfloat('options', 'value2') == 42.0
    assert isinstance(config.getfloat('options', 'value2'), float)
    assert config.getfloat('options', 'missing') is None
    assert config.getfloat('options', 'missing', 3.14) == 3.14
    # default is not converted!
    assert config.getfloat('options', 'missing', '3.14') == '3.14'

    with pytest.raises(ValueError):
        config.getfloat('options', 'value3')

    with pytest.raises(ValueError):
        config.getfloat('options', 'value4')


def test_config_getlist(mock, watson):
    content = u"""
# empty lines in option values (including the first one) are discarded
[options]
value1 =
    one

    two three
    four
    five six
# multiple inner space preserved
value2 = one  "two three" four 'five  six'
value3 = one
    two  three
# outer space stripped
value4 = one
     two three
    four
# hash char not at start of line does not start comment
value5 = one
   two #three
   four # five
"""
    mock.patch.object(ConfigParser, 'read', mock_read(content))
    gl = watson.config.getlist
    assert gl('options', 'value1') == ['one', 'two three', 'four',
                                       'five six']
    assert gl('options', 'value2') == ['one', 'two three', 'four',
                                       'five  six']
    assert gl('options', 'value3') == ['one', 'two  three']
    assert gl('options', 'value4') == ['one', 'two three', 'four']
    assert gl('options', 'value5') == ['one', 'two #three', 'four # five']

    # default values
    assert gl('options', 'novalue') == []
    assert gl('options', 'novalue', None) == []
    assert gl('options', 'novalue', 42) == 42
    assert gl('nosection', 'dummy') == []
    assert gl('nosection', 'dummy', None) == []
    assert gl('nosection', 'dummy', 42) == 42

    default = gl('nosection', 'dummy')
    default.append(42)
    assert gl('nosection', 'dummy') != [42], (
        "Modifying default return value should not have side effect.")


def test_set_config(watson):
    config = ConfigParser()
    config.set('foo', 'bar', 'lol')
    watson.config = config

    assert watson.config.get('foo', 'bar') == 'lol'
