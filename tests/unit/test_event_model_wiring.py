"""Cycle 13: WineRadar event_model_payload wiring tests.

Verifies that ``_attach_wine_event_model_payload`` stashes a contract-bound
payload on ``Article.ontology["event_model_payload"]`` for sources whose
canonical Article fields fully cover the WineRadar runtime contract's
required_fields, and skips sources outside the curated mapping table.
"""

from __future__ import annotations

from datetime import datetime, timezone

from main import (
    _attach_wine_event_model_payload,
    _resolve_event_model_key,
)
from wineradar import models as radar_models


def _build_article(
    *,
    title: str = "Bordeaux 2024 Vintage Outlook",
    link: str = "https://example.com/bordeaux-2024",
    summary: str = "Trade media commentary on the 2024 Bordeaux harvest.",
    published: datetime | None = datetime(2024, 3, 15, 9, 30, tzinfo=timezone.utc),
    source: str = "Decanter",
) -> radar_models.Article:
    return radar_models.Article(
        title=title,
        link=link,
        summary=summary,
        published=published,
        source=source,
        category="wine",
        matched_entities={"Bordeaux": ["bordeaux"]},
    )


def test_resolve_event_model_key_for_mapped_source() -> None:
    article = _build_article(source="Wine Spectator")
    assert _resolve_event_model_key(article) == "market_report"


def test_resolve_event_model_key_for_community_source() -> None:
    article = _build_article(source="r/wine")
    assert _resolve_event_model_key(article) == "daily_briefing"


def test_resolve_event_model_key_unmappable_source_returns_none() -> None:
    article = _build_article(source="Some Random Wine Blog")
    assert _resolve_event_model_key(article) is None


def test_attach_payload_full_mapping_for_market_report_source() -> None:
    """Decanter → market_report; canonical title/published/link satisfy all
    three required_fields (title, published_date, source_url)."""
    article = _build_article(source="Decanter")
    _attach_wine_event_model_payload(article)
    payload = article.ontology.get("event_model_payload")
    assert payload is not None
    assert payload == {
        "title": "Bordeaux 2024 Vintage Outlook",
        "published_date": "2024-03-15T09:30:00+00:00",
        "source_url": "https://example.com/bordeaux-2024",
    }


def test_attach_payload_skips_unmappable_source() -> None:
    """Sources outside the mapping table leave Article.ontology untouched."""
    article = _build_article(source="Some Random Wine Blog")
    _attach_wine_event_model_payload(article)
    assert "event_model_payload" not in article.ontology


def test_attach_payload_partial_when_published_missing() -> None:
    """When ``published`` is None the payload still attaches with the fields
    it could populate (title + source_url) — partial coverage is contract-
    compliant since required_fields validation happens elsewhere."""
    article = _build_article(source="The Drinks Business", published=None)
    _attach_wine_event_model_payload(article)
    payload = article.ontology.get("event_model_payload")
    assert payload is not None
    # published_date drops out (None override is not applied; attribute fallback
    # for `published_date` also returns None on the canonical Article).
    assert payload == {
        "title": "Bordeaux 2024 Vintage Outlook",
        "source_url": "https://example.com/bordeaux-2024",
    }
