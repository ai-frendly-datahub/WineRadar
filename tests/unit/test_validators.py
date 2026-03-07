from __future__ import annotations

from datetime import datetime

import pytest

from wineradar.common.validators import (
    detect_duplicate_articles,
    is_similar_url,
    normalize_title,
    validate_article,
    validate_rating,
    validate_url_format,
    validate_vintage,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_title", "expected"),
    [
        ("Bordeaux Market Update", "bordeaux market update"),
        ("  Napa   Vintage  ", "napa vintage"),
        ("Chateau (Reserve)", "chateau reserve"),
        ("Wine-Score", "wine-score"),
        ("", ""),
        ("샤또 마고", "샤또 마고"),
    ],
)
def test_normalize_title(raw_title: str, expected: str) -> None:
    assert normalize_title(raw_title) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.com/wine/1", True),
        ("http://example.com/wine/1", True),
        ("example.com/wine/1", False),
        ("", False),
        (None, False),
    ],
)
def test_validate_url_format(url: str, expected: bool) -> None:
    assert validate_url_format(url) is expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("url1", "url2", "threshold", "expected"),
    [
        ("https://example.com/wine/1", "https://example.com/wine/1", 0.8, True),
        ("https://example.com/wine/1", "https://example.com/wine/1?ref=rss", 0.8, True),
        ("https://example.com/wine/1", "https://other.com/wine/1", 0.8, False),
        ("https://example.com/wine/1", "https://example.com/wine/2", 0.95, False),
        ("https://example.com/wine/1", "https://example.com/wine/2", 0.5, True),
    ],
)
def test_is_similar_url(url1: str, url2: str, threshold: float, expected: bool) -> None:
    assert is_similar_url(url1, url2, threshold=threshold) is expected


@pytest.mark.unit
def test_detect_duplicate_articles() -> None:
    assert (
        detect_duplicate_articles(
            "Bordeaux report",
            "https://example.com/wine/1",
            "Bordeaux report",
            "https://example.com/wine/1?ref=rss",
        )
        is True
    )


@pytest.mark.unit
def test_validate_article_valid_dict() -> None:
    article = {
        "title": "Wine title",
        "url": "https://example.com/wine/1",
        "summary": "summary",
        "source_name": "wine-searcher",
        "content_type": "market_report",
    }
    is_valid, errors = validate_article(article)
    assert is_valid is True
    assert errors == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "article",
    [
        {"title": "", "url": "https://example.com", "summary": "x", "source": "s", "category": "c"},
        {"title": "t", "url": "bad", "summary": "x", "source": "s", "category": "c"},
        {"title": "t", "url": "https://example.com", "summary": "", "source": "s", "category": "c"},
        {"title": "t", "url": "https://example.com", "summary": "x", "source": "", "category": "c"},
        {"title": "t", "url": "https://example.com", "summary": "x", "source": "s", "category": ""},
    ],
)
def test_validate_article_invalid_cases(article: dict[str, str]) -> None:
    is_valid, errors = validate_article(article)
    assert is_valid is False
    assert errors


@pytest.mark.unit
@pytest.mark.parametrize(
    ("rating", "expected"),
    [
        (None, True),
        (0.0, True),
        (5.0, True),
        (3.7, True),
        (-0.1, False),
        (5.1, False),
    ],
)
def test_validate_rating(rating: float | None, expected: bool) -> None:
    assert validate_rating(rating) is expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("vintage", "expected"),
    [
        (None, True),
        (1900, True),
        (datetime.now().year, True),
        (1899, False),
        (datetime.now().year + 1, False),
    ],
)
def test_validate_vintage(vintage: int | None, expected: bool) -> None:
    assert validate_vintage(vintage) is expected
