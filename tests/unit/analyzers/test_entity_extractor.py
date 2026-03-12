"""엔티티 추출기 테스트."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import analyzers.entity_extractor as entity_extractor_module
from collectors.base import RawItem
from analyzers.entity_extractor import (
    extract_grape_varieties,
    extract_regions,
    extract_wineries,
    extract_all_entities,
    infer_climate_zone,
)

pytestmark = pytest.mark.unit


def test_extract_grape_varieties_from_title() -> None:
    """제목에서 포도 품종 추출."""
    item: RawItem = {
        "id": "test-1",
        "url": "https://example.com/wine/1",
        "title": "Cabernet Sauvignon and Merlot Blend from Bordeaux",
        "summary": None,
        "content": None,
        "published_at": datetime(2025, 1, 19, tzinfo=timezone.utc),
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "FR",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/France",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C1_rss",
    }

    entities = extract_grape_varieties(item)

    assert len(entities) == 2
    assert any(e["value"] == "Cabernet Sauvignon" and e["confidence"] == 1.0 for e in entities)
    assert any(e["value"] == "Merlot" and e["confidence"] == 1.0 for e in entities)


def test_extract_regions_from_summary() -> None:
    """요약에서 와인 산지 추출."""
    item: RawItem = {
        "id": "test-2",
        "url": "https://example.com/wine/2",
        "title": "Wine News",
        "summary": "Exploring the wines of Napa Valley and Sonoma",
        "content": None,
        "published_at": datetime(2025, 1, 19, tzinfo=timezone.utc),
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "US",
        "continent": "NEW_WORLD",
        "region": "Americas/North/USA",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P4_trend_discovery"],
        "collection_tier": "C1_rss",
    }

    entities = extract_regions(item)

    assert len(entities) == 2
    assert any(e["value"] == "Napa Valley" and e["confidence"] == 0.8 for e in entities)
    assert any(e["value"] == "Sonoma" and e["confidence"] == 0.8 for e in entities)


def test_extract_wineries() -> None:
    """와이너리명 추출."""
    item: RawItem = {
        "id": "test-3",
        "url": "https://example.com/wine/3",
        "title": "Château Lafite Releases 2020 Vintage",
        "summary": "Opus One and Penfolds also announce new vintages",
        "content": "Antinori in Tuscany is leading the way...",
        "published_at": datetime(2025, 1, 19, tzinfo=timezone.utc),
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "FR",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/France",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C1_rss",
    }

    entities = extract_wineries(item)

    assert len(entities) >= 3
    # title에서 1.0 신뢰도
    assert any(e["value"] == "Château Lafite" and e["confidence"] == 1.0 for e in entities)
    # summary에서 0.8 신뢰도
    assert any(e["value"] == "Opus One" and e["confidence"] == 0.8 for e in entities)
    assert any(e["value"] == "Penfolds" and e["confidence"] == 0.8 for e in entities)
    # content에서 0.6 신뢰도
    assert any(e["value"] == "Antinori" and e["confidence"] == 0.6 for e in entities)


def test_infer_climate_zone() -> None:
    """지역으로부터 기후대 추론."""
    # Bordeaux -> Mediterranean
    region_entities: list[entity_extractor_module.Entity] = [
        {
            "type": "region",
            "value": "Bordeaux",
            "confidence": 1.0,
            "source": "title",
        }
    ]

    climate_entities = infer_climate_zone(region_entities)

    assert len(climate_entities) == 1
    assert climate_entities[0]["value"] == "Mediterranean"
    assert climate_entities[0]["confidence"] == 0.9  # 1.0 * 0.9


def test_extract_all_entities_comprehensive() -> None:
    """전체 엔티티 추출 통합 테스트."""
    item: RawItem = {
        "id": "test-4",
        "url": "https://example.com/wine/4",
        "title": "Château Margaux Cabernet Sauvignon 2020",
        "summary": "A masterpiece from Bordeaux featuring Merlot blend",
        "content": "The wine showcases classic Pinot Noir characteristics from Burgundy...",
        "published_at": datetime(2025, 1, 19, tzinfo=timezone.utc),
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "FR",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/France",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C1_rss",
    }

    entities = extract_all_entities(item)

    # 포도 품종 (title + summary + content)
    assert "grape_variety" in entities
    assert "Cabernet Sauvignon" in entities["grape_variety"]
    assert "Merlot" in entities["grape_variety"]
    assert "Pinot Noir" in entities["grape_variety"]

    # 지역 (summary + content)
    assert "region" in entities
    assert "Bordeaux" in entities["region"]
    assert "Burgundy" in entities["region"]

    # 와이너리 (title)
    assert "winery" in entities
    assert "Château Margaux" in entities["winery"]

    # 기후대 (추론)
    assert "climate_zone" in entities
    assert "Mediterranean" in entities["climate_zone"] or "Continental" in entities["climate_zone"]


def test_keyword_in_text_uses_kiwi_for_non_ascii(monkeypatch) -> None:
    class _KiwiAnalyzerStub:
        def __init__(self) -> None:
            self._kiwi = object()
            self.called = False

        def match_keyword(self, text: str, keyword: str) -> bool:
            self.called = True
            return keyword == "샤또마고" and "샤또 마고" in text

    kiwi_stub = _KiwiAnalyzerStub()
    monkeypatch.setattr(entity_extractor_module, "_korean_analyzer", kiwi_stub, raising=False)
    monkeypatch.setattr(
        entity_extractor_module, "_korean_analyzer_initialized", True, raising=False
    )

    assert entity_extractor_module._keyword_in_text("샤또마고", "샤또 마고 출시", "샤또 마고 출시")
    assert kiwi_stub.called is True


def test_extract_all_entities_empty_text() -> None:
    """빈 텍스트에서 엔티티 추출."""
    item: RawItem = {
        "id": "test-5",
        "url": "https://example.com/wine/5",
        "title": "",
        "summary": None,
        "content": None,
        "published_at": datetime(2025, 1, 19, tzinfo=timezone.utc),
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "US",
        "continent": "NEW_WORLD",
        "region": "Americas/North/USA",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C1_rss",
    }

    entities = extract_all_entities(item)

    assert entities == {}


def test_extract_entities_confidence_filtering() -> None:
    """신뢰도 필터링 테스트."""
    # content에만 있는 품종 (confidence 0.6)은 threshold 0.5 초과로 포함
    item: RawItem = {
        "id": "test-6",
        "url": "https://example.com/wine/6",
        "title": "Wine News",
        "summary": None,
        "content": "This Chardonnay is excellent...",
        "published_at": datetime(2025, 1, 19, tzinfo=timezone.utc),
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "FR",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/France",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C1_rss",
    }

    entities = extract_all_entities(item)

    assert "grape_variety" in entities
    assert "Chardonnay" in entities["grape_variety"]


def test_extract_entities_case_insensitive() -> None:
    """대소문자 무시 매칭."""
    item: RawItem = {
        "id": "test-7",
        "url": "https://example.com/wine/7",
        "title": "bordeaux CABERNET sauvignon",  # 소문자/대문자 혼합
        "summary": None,
        "content": None,
        "published_at": datetime(2025, 1, 19, tzinfo=timezone.utc),
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "FR",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/France",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C1_rss",
    }

    entities = extract_all_entities(item)

    assert "grape_variety" in entities
    assert "Cabernet Sauvignon" in entities["grape_variety"]

    assert "region" in entities
    assert "Bordeaux" in entities["region"]


def test_extract_entities_no_duplicates() -> None:
    """중복 제거 검증."""
    item: RawItem = {
        "id": "test-8",
        "url": "https://example.com/wine/8",
        "title": "Bordeaux Bordeaux Bordeaux",  # 중복
        "summary": "Bordeaux is great",  # 중복
        "content": "I love Bordeaux",  # 중복
        "published_at": datetime(2025, 1, 19, tzinfo=timezone.utc),
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "FR",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/France",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C1_rss",
    }

    entities = extract_all_entities(item)

    assert "region" in entities
    assert len(entities["region"]) == 1  # 중복 제거됨
    assert entities["region"][0] == "Bordeaux"
