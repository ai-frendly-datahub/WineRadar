from __future__ import annotations

import pytest

from nl_query import parse_query


@pytest.mark.unit
def test_parse_time_filter_days_korean() -> None:
    parsed = parse_query("최근 3일 와인")

    assert parsed.days == 3
    assert "와인" in parsed.search_text


@pytest.mark.unit
def test_parse_time_filter_weeks_korean() -> None:
    parsed = parse_query("지난 2주 보르도 뉴스")

    assert parsed.days == 14
    assert "보르도" in parsed.search_text


@pytest.mark.unit
def test_parse_time_filter_months_english() -> None:
    parsed = parse_query("last 2 months wine export")

    assert parsed.days == 60
    assert "wine" in parsed.search_text


@pytest.mark.unit
def test_parse_limit_korean_and_english() -> None:
    assert parse_query("와인 시장 10개").limit == 10
    assert parse_query("top 5 bordeaux").limit == 5


@pytest.mark.unit
def test_parse_combined_filters_and_whitespace_cleanup() -> None:
    parsed = parse_query("  최근 1주   보르도   와인   3개  ")

    assert parsed.days == 7
    assert parsed.limit == 3
    assert parsed.search_text == "보르도 와인"
    assert parsed.category is None


@pytest.mark.unit
def test_parse_without_filters() -> None:
    parsed = parse_query("cabernet sauvignon")

    assert parsed.days is None
    assert parsed.limit is None
    assert parsed.search_text == "cabernet sauvignon"
