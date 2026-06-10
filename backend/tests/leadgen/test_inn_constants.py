"""Канон ИНН leadgen — мок vs live."""

from leadgen.inn_constants import LIVE_INN_HOCHLAND, MOCK_INN_TECHNOSOFT


def test_inn_constants_distinct_ten_digits():
    assert len(LIVE_INN_HOCHLAND) == 10
    assert len(MOCK_INN_TECHNOSOFT) == 10
    assert LIVE_INN_HOCHLAND != MOCK_INN_TECHNOSOFT
