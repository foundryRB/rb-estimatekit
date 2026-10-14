"""Tests for the shared Rate Day parser."""

from __future__ import annotations

import pytest

from engine.domain.exceptions import InvalidRateError
from engine.domain.services.rate_parser import parse_rate_day


class TestParseRateDay:
    """Rate Day cells parse tolerantly; unparsable values fail loudly."""

    def test_plain_number(self) -> None:
        assert parse_rate_day("360", context="t") == 360.0

    def test_currency_symbol_prefix(self) -> None:
        assert parse_rate_day("€ 360", context="t") == 360.0

    def test_currency_code_prefix(self) -> None:
        assert parse_rate_day("EUR 350", context="t") == 350.0

    def test_comma_decimal(self) -> None:
        assert parse_rate_day("350,5", context="t") == 350.5

    def test_empty_is_zero(self) -> None:
        assert parse_rate_day("", context="t") == 0.0
        assert parse_rate_day("   ", context="t") == 0.0

    def test_unparsable_value_raises_with_context(self) -> None:
        with pytest.raises(InvalidRateError) as excinfo:
            parse_rate_day("TBD", context="phase P1, stream 'Delivery'")
        assert excinfo.value.value == "TBD"
        assert "P1" in str(excinfo.value)

    def test_multiple_decimal_points_raise(self) -> None:
        with pytest.raises(InvalidRateError):
            parse_rate_day("1.234,50", context="t")
