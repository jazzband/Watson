"""Unit test for the 'fullmoon' helper"""

import arrow
import pytest

from watson.fullmoon import get_last_full_moon


def test_with_known_date():
    aniceday = arrow.Arrow(2018, 7, 27, 10, 51)
    aniceday_lastMoon = arrow.Arrow(2018, 6, 28, 4, 55)
    aniceday_result = get_last_full_moon(aniceday)
    assert aniceday_result == aniceday_lastMoon
    thenextday = aniceday.shift(days=1)
    thenextday_lastMoon = arrow.Arrow(2018, 7, 27, 20, 22)
    thenextday_result = get_last_full_moon(thenextday)
    assert thenextday_result == thenextday_lastMoon


def test_invalid_ranges():
    fail = arrow.Arrow(1970, 1, 1)
    fail2 = arrow.Arrow(2100, 5, 5)
    with pytest.raises(ValueError):
        get_last_full_moon(fail)
    with pytest.raises(ValueError):
        get_last_full_moon(fail2)
