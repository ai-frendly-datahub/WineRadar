"""config/sources.yaml 검증."""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.unit

REQUIRED_KEYS = {
    "name",
    "id",
    "type",
    "enabled",
    "weight",
    "config",
    "continent",
    "country",
    "region",
    "producer_role",
    "tier",
    "trust_tier",
    "info_purpose",
    "collection_tier",
    "supports_rss",
    "requires_login",
}

ALLOWED_TRUST_TIERS = {"T1_authoritative", "T2_expert", "T3_professional"}
ALLOWED_COLLECTION_TIERS = {"C1_rss", "C2_html_simple", "C3_html_js", "C5_manual"}
ALLOWED_INFO_PURPOSE = {
    "P1_daily_briefing",
    "P2_market_analysis",
    "P3_investment",
    "P4_trend_discovery",
    "P5_education",
}


def test_sources_entries_have_minimum_fields(sources_config: dict[str, Any]) -> None:
    sources = sources_config.get("sources", [])
    assert sources, "최소 한 개 이상의 source 정의가 필요합니다."

    for source in sources:
        assert REQUIRED_KEYS <= set(source), f"필수 키 누락: {source}"
        assert isinstance(source["config"], dict), "config는 dict 여야 합니다."
        assert source["trust_tier"] in ALLOWED_TRUST_TIERS
        assert source["collection_tier"] in ALLOWED_COLLECTION_TIERS
        info_purpose = source["info_purpose"]
        assert isinstance(info_purpose, list) and info_purpose, "info_purpose 리스트 필요"
        assert set(info_purpose) <= ALLOWED_INFO_PURPOSE


def test_enabled_sources_have_list_url(sources_config: dict[str, Any]) -> None:
    for source in sources_config.get("sources", []):
        if not source.get("enabled", False):
            continue
        list_url = source["config"].get("list_url")
        assert (
            isinstance(list_url, str) and list_url.startswith("https://")
        ), f"list_url 형식 오류: {source['id']}"


def test_at_least_one_rss_source_is_enabled(sources_config: dict[str, Any]) -> None:
    rss_sources = [
        src
        for src in sources_config.get("sources", [])
        if src.get("supports_rss") and src.get("enabled")
    ]
    assert rss_sources, "supports_rss=true 이면서 enabled=true 인 소스가 최소 1개 이상 필요합니다."
