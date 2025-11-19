"""RawItem TypedDict 사용자 뷰 중심 메타데이터 타입 검증 테스트."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, get_type_hints

import pytest

from collectors.base import (
    RawItem,
    Continent,
    ProducerRole,
    TrustTier,
    InfoPurpose,
    CollectionTier,
)

pytestmark = pytest.mark.unit


def test_raw_item_has_required_fields() -> None:
    """RawItem TypedDict가 모든 필수 필드를 정의하고 있는지 검증."""
    type_hints = get_type_hints(RawItem)

    required_fields = {
        # 콘텐츠 필드
        "id",
        "url",
        "title",
        "summary",
        "content",
        "published_at",
        "source_name",
        "source_type",
        "language",
        "content_type",
        # 사용자 뷰 중심 메타데이터
        "country",
        "continent",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
    }

    actual_fields = set(type_hints.keys())
    assert required_fields == actual_fields, (
        f"RawItem 필드 불일치. "
        f"누락: {required_fields - actual_fields}, "
        f"초과: {actual_fields - required_fields}"
    )


def test_raw_item_metadata_types() -> None:
    """RawItem 메타데이터 필드의 타입이 올바른지 검증."""
    type_hints = get_type_hints(RawItem)

    # 문자열 필드
    assert type_hints["id"] == str
    assert type_hints["url"] == str
    assert type_hints["title"] == str
    assert type_hints["source_name"] == str
    assert type_hints["source_type"] == str
    assert type_hints["content_type"] == str
    assert type_hints["country"] == str
    assert type_hints["region"] == str

    # Optional 문자열 필드
    assert type_hints["summary"] == str | None
    assert type_hints["content"] == str | None
    assert type_hints["language"] == str | None

    # datetime 필드
    assert type_hints["published_at"] == datetime

    # Literal 타입 필드
    assert type_hints["continent"] == Continent
    assert type_hints["producer_role"] == ProducerRole
    assert type_hints["trust_tier"] == TrustTier
    assert type_hints["collection_tier"] == CollectionTier

    # 배열 필드
    assert type_hints["info_purpose"] == list[InfoPurpose]


def test_continent_literal_values() -> None:
    """Continent Literal이 올바른 값을 가지는지 검증."""
    # Literal 타입의 값 추출
    import typing

    continent_args = typing.get_args(Continent)
    expected = {"OLD_WORLD", "NEW_WORLD", "ASIA"}

    assert set(continent_args) == expected, (
        f"Continent 값 불일치. 예상: {expected}, 실제: {set(continent_args)}"
    )


def test_producer_role_literal_values() -> None:
    """ProducerRole Literal이 올바른 값을 가지는지 검증."""
    import typing

    role_args = typing.get_args(ProducerRole)
    expected = {
        "government",
        "industry_assoc",
        "research_inst",
        "expert_media",
        "trade_media",
        "importer",
        "consumer_comm",
    }

    assert set(role_args) == expected, (
        f"ProducerRole 값 불일치. 예상: {expected}, 실제: {set(role_args)}"
    )


def test_trust_tier_literal_values() -> None:
    """TrustTier Literal이 올바른 값을 가지는지 검증."""
    import typing

    tier_args = typing.get_args(TrustTier)
    expected = {
        "T1_authoritative",
        "T2_expert",
        "T3_professional",
        "T4_community",
    }

    assert set(tier_args) == expected, (
        f"TrustTier 값 불일치. 예상: {expected}, 실제: {set(tier_args)}"
    )


def test_info_purpose_literal_values() -> None:
    """InfoPurpose Literal이 올바른 값을 가지는지 검증."""
    import typing

    purpose_args = typing.get_args(InfoPurpose)
    expected = {
        "P1_daily_briefing",
        "P2_market_analysis",
        "P3_investment",
        "P4_trend_discovery",
        "P5_education",
    }

    assert set(purpose_args) == expected, (
        f"InfoPurpose 값 불일치. 예상: {expected}, 실제: {set(purpose_args)}"
    )


def test_collection_tier_literal_values() -> None:
    """CollectionTier Literal이 올바른 값을 가지는지 검증."""
    import typing

    tier_args = typing.get_args(CollectionTier)
    expected = {
        "C1_rss",
        "C2_html_simple",
        "C3_html_js",
        "C4_api",
        "C5_manual",
    }

    assert set(tier_args) == expected, (
        f"CollectionTier 값 불일치. 예상: {expected}, 실제: {set(tier_args)}"
    )


def test_raw_item_instantiation_with_valid_data() -> None:
    """올바른 데이터로 RawItem을 생성할 수 있는지 검증."""
    valid_item: RawItem = {
        # 콘텐츠 필드
        "id": "test_decanter_001",
        "url": "https://www.decanter.com/wine-news/test-001",
        "title": "Test Wine News",
        "summary": "Test summary",
        "content": "Test content",
        "published_at": datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        "source_name": "Decanter",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        # 사용자 뷰 중심 메타데이터
        "country": "GB",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/United Kingdom",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing", "P4_trend_discovery"],
        "collection_tier": "C1_rss",
    }

    # TypedDict는 런타임 타입 체크를 하지 않으므로,
    # 모든 필드가 존재하는지만 확인
    type_hints = get_type_hints(RawItem)
    for field in type_hints.keys():
        assert field in valid_item, f"필수 필드 '{field}' 누락"


def test_raw_item_metadata_consistency() -> None:
    """RawItem 메타데이터가 sources.yaml 규칙과 일치하는지 검증."""
    # producer_role과 trust_tier의 일관성
    valid_combinations = {
        "government": "T1_authoritative",
        "industry_assoc": "T1_authoritative",
        "research_inst": "T1_authoritative",
        "expert_media": "T2_expert",
        "trade_media": "T3_professional",
        "importer": "T3_professional",
        "consumer_comm": "T4_community",
    }

    # 각 조합이 타입 시스템에 의해 허용되는지 확인
    import typing

    producer_roles = typing.get_args(ProducerRole)
    trust_tiers = typing.get_args(TrustTier)

    for role, expected_tier in valid_combinations.items():
        assert role in producer_roles, f"ProducerRole에 '{role}' 누락"
        assert expected_tier in trust_tiers, f"TrustTier에 '{expected_tier}' 누락"


def test_raw_item_all_literal_types_are_exported() -> None:
    """모든 Literal 타입이 base.py에서 export되는지 검증."""
    from collectors.base import (
        Continent,
        ProducerRole,
        TrustTier,
        InfoPurpose,
        CollectionTier,
    )

    # Import 성공하면 테스트 통과
    assert Continent is not None
    assert ProducerRole is not None
    assert TrustTier is not None
    assert InfoPurpose is not None
    assert CollectionTier is not None


def test_raw_item_info_purpose_is_list() -> None:
    """info_purpose 필드가 배열 타입인지 검증."""
    type_hints = get_type_hints(RawItem)

    # list[InfoPurpose] 타입인지 확인
    import typing

    assert typing.get_origin(type_hints["info_purpose"]) == list, (
        "info_purpose는 list 타입이어야 함"
    )

    # 리스트 요소 타입이 InfoPurpose인지 확인
    list_args = typing.get_args(type_hints["info_purpose"])
    assert len(list_args) == 1
    assert list_args[0] == InfoPurpose


def test_raw_item_optional_fields() -> None:
    """RawItem의 Optional 필드가 올바르게 정의되었는지 검증."""
    type_hints = get_type_hints(RawItem)

    optional_fields = ["summary", "content", "language"]

    for field in optional_fields:
        field_type = type_hints[field]
        # str | None 타입인지 확인
        assert field_type == str | None, (
            f"{field}는 str | None 타입이어야 함 (현재: {field_type})"
        )


def test_raw_item_matches_sources_yaml_metadata() -> None:
    """RawItem 메타데이터 필드가 sources.yaml 필드와 정확히 일치하는지 검증."""
    type_hints = get_type_hints(RawItem)

    # sources.yaml의 사용자 뷰 중심 메타데이터 필드
    sources_yaml_metadata = {
        "country",
        "continent",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
    }

    # RawItem의 메타데이터 필드
    raw_item_metadata = {
        field
        for field in type_hints.keys()
        if field
        in {
            "country",
            "continent",
            "region",
            "producer_role",
            "trust_tier",
            "info_purpose",
            "collection_tier",
        }
    }

    assert sources_yaml_metadata == raw_item_metadata, (
        f"RawItem 메타데이터가 sources.yaml과 불일치. "
        f"누락: {sources_yaml_metadata - raw_item_metadata}, "
        f"초과: {raw_item_metadata - sources_yaml_metadata}"
    )
