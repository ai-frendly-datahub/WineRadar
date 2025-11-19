"""sources.yaml 메타데이터 parameterized 테스트."""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.unit


# 모든 소스의 (producer_role, expected_trust_tier) 조합 테스트
@pytest.mark.parametrize(
    "producer_role,expected_trust_tier",
    [
        ("government", "T1_authoritative"),
        ("industry_assoc", "T1_authoritative"),
        ("research_inst", "T1_authoritative"),
        ("expert_media", "T2_expert"),
        ("trade_media", "T3_professional"),
        ("importer", "T3_professional"),
        ("consumer_comm", "T4_community"),
    ],
)
def test_producer_role_trust_tier_mapping(
    sources_config: dict[str, Any], producer_role: str, expected_trust_tier: str
) -> None:
    """각 producer_role에 대한 trust_tier 매핑이 정확한지 검증."""
    sources = sources_config.get("sources", [])

    matching_sources = [s for s in sources if s.get("producer_role") == producer_role]

    if matching_sources:
        for source in matching_sources:
            source_id = source.get("id", "unknown")
            actual_tier = source.get("trust_tier")
            assert actual_tier == expected_trust_tier, (
                f"{source_id}: producer_role '{producer_role}'에 대해 "
                f"trust_tier '{actual_tier}'가 설정되었으나 '{expected_trust_tier}'여야 함"
            )


@pytest.mark.parametrize(
    "continent,valid_prefixes",
    [
        ("OLD_WORLD", ["Europe/", "Africa/North", "Africa/East", "Middle East/"]),
        ("NEW_WORLD", ["Americas/", "Oceania/", "Africa/South"]),
        ("ASIA", ["Asia/"]),
    ],
)
def test_continent_region_prefix_mapping(
    sources_config: dict[str, Any], continent: str, valid_prefixes: list[str]
) -> None:
    """각 continent에 대한 region prefix가 올바른지 검증."""
    sources = sources_config.get("sources", [])

    matching_sources = [s for s in sources if s.get("continent") == continent]

    for source in matching_sources:
        source_id = source.get("id", "unknown")
        region = source.get("region", "")

        has_valid_prefix = any(region.startswith(prefix) for prefix in valid_prefixes)
        assert has_valid_prefix, (
            f"{source_id}: continent '{continent}'에 대해 "
            f"region '{region}'이 유효하지 않음. "
            f"유효한 prefix: {valid_prefixes}"
        )


@pytest.mark.parametrize(
    "trust_tier,min_weight,max_weight",
    [
        ("T1_authoritative", 2.0, 2.5),
        ("T2_expert", 2.8, 3.0),
        ("T3_professional", 2.0, 2.8),
        ("T4_community", 1.5, 2.5),
    ],
)
def test_trust_tier_weight_range_mapping(
    sources_config: dict[str, Any], trust_tier: str, min_weight: float, max_weight: float
) -> None:
    """각 trust_tier에 대한 weight 범위가 올바른지 검증."""
    sources = sources_config.get("sources", [])

    matching_sources = [s for s in sources if s.get("trust_tier") == trust_tier]

    for source in matching_sources:
        source_id = source.get("id", "unknown")
        weight = source.get("weight", 0)

        assert min_weight <= weight <= max_weight, (
            f"{source_id}: trust_tier '{trust_tier}'에 대해 "
            f"weight {weight}는 범위를 벗어남. "
            f"예상 범위: {min_weight} ~ {max_weight}"
        )


@pytest.mark.parametrize(
    "collection_method,expected_tier",
    [
        ("rss", "C1_rss"),
        ("html", ["C2_html_simple", "C3_html_js", "C5_manual"]),  # C5_manual 추가 (페이월 케이스)
        ("api", "C4_api"),
    ],
)
def test_collection_method_tier_mapping(
    sources_config: dict[str, Any], collection_method: str, expected_tier: str | list[str]
) -> None:
    """collection_method에 대한 collection_tier 매핑이 올바른지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        config = source.get("config", {})
        actual_method = config.get("collection_method")

        if actual_method == collection_method:
            actual_tier = source.get("collection_tier")

            if isinstance(expected_tier, list):
                assert actual_tier in expected_tier, (
                    f"{source_id}: collection_method '{collection_method}'에 대해 "
                    f"collection_tier '{actual_tier}'가 설정되었으나 "
                    f"{expected_tier} 중 하나여야 함"
                )
            else:
                assert actual_tier == expected_tier, (
                    f"{source_id}: collection_method '{collection_method}'에 대해 "
                    f"collection_tier '{actual_tier}'가 설정되었으나 '{expected_tier}'여야 함"
                )


@pytest.mark.parametrize(
    "info_purpose,valid_content_types",
    [
        ("P1_daily_briefing", ["news_review"]),
        ("P2_market_analysis", ["statistics", "market_report"]),
        ("P3_investment", ["news_review", "expert_rating"]),
        ("P4_trend_discovery", ["news_review"]),
        ("P5_education", ["education", "statistics"]),
    ],
)
def test_info_purpose_content_type_mapping(
    sources_config: dict[str, Any], info_purpose: str, valid_content_types: list[str]
) -> None:
    """info_purpose에 대한 content_type 매핑이 올바른지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        purposes = source.get("info_purpose", [])
        content_type = source.get("content_type", "")

        if info_purpose in purposes:
            assert content_type in valid_content_types, (
                f"{source_id}: info_purpose '{info_purpose}'에 대해 "
                f"content_type '{content_type}'는 유효하지 않음. "
                f"유효한 타입: {valid_content_types}"
            )


@pytest.mark.parametrize(
    "country_code",
    ["GB", "IT", "FR", "US", "CL", "AR", "ES", "AU", "KR", "ZA", "NZ", "DE", "PT"],
)
def test_country_codes_are_uppercase(sources_config: dict[str, Any], country_code: str) -> None:
    """특정 국가 코드가 대문자로 정의되었는지 검증."""
    sources = sources_config.get("sources", [])

    matching_sources = [s for s in sources if s.get("country") == country_code]

    for source in matching_sources:
        country = source.get("country", "")
        assert country.isupper(), f"{source.get('id')}: country '{country}'는 대문자여야 함"
        assert len(country) == 2, f"{source.get('id')}: country '{country}'는 2글자여야 함"


@pytest.mark.parametrize(
    "field_name,expected_type",
    [
        ("country", str),
        ("continent", str),
        ("region", str),
        ("producer_role", str),
        ("trust_tier", str),
        ("collection_tier", str),
        ("info_purpose", list),
        ("enabled", bool),
        ("weight", (int, float)),
    ],
)
def test_metadata_field_type(sources_config: dict[str, Any], field_name: str, expected_type: type | tuple) -> None:
    """각 메타데이터 필드의 타입이 올바른지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        value = source.get(field_name)

        assert isinstance(value, expected_type), (
            f"{source_id}: {field_name}는 {expected_type} 타입이어야 함 "
            f"(현재: {type(value)})"
        )


@pytest.mark.parametrize(
    "source_id",
    [
        "media_decanter_global",
        "media_gambero_it",
        "official_wineinstitute_us",  # 수정됨
        "official_ifv_fr",
        "media_wine21_kr",
        "media_winereview_kr",  # 수정됨
    ],
)
def test_key_sources_exist(sources_config: dict[str, Any], source_id: str) -> None:
    """핵심 소스가 sources.yaml에 정의되어 있는지 검증."""
    sources = sources_config.get("sources", [])
    source_ids = {s.get("id") for s in sources}

    assert source_id in source_ids, f"핵심 소스 '{source_id}'가 정의되지 않음"


@pytest.mark.parametrize(
    "phase1_source_id",
    [
        "media_decanter_global",
        "media_gambero_it",
    ],
)
def test_phase1_sources_configuration(sources_config: dict[str, Any], phase1_source_id: str) -> None:
    """Phase 1 소스가 올바르게 설정되었는지 검증."""
    sources = sources_config.get("sources", [])

    source = next((s for s in sources if s.get("id") == phase1_source_id), None)
    assert source is not None, f"Phase 1 소스 '{phase1_source_id}'가 존재하지 않음"

    # enabled=true
    assert source.get("enabled") is True, (
        f"{phase1_source_id}: Phase 1 소스는 enabled=true여야 함"
    )

    # collection_tier=C1_rss
    assert source.get("collection_tier") == "C1_rss", (
        f"{phase1_source_id}: Phase 1 소스는 C1_rss여야 함"
    )

    # trust_tier=T2_expert
    assert source.get("trust_tier") == "T2_expert", (
        f"{phase1_source_id}: Phase 1 소스는 T2_expert여야 함"
    )

    # producer_role=expert_media
    assert source.get("producer_role") == "expert_media", (
        f"{phase1_source_id}: Phase 1 소스는 expert_media여야 함"
    )


@pytest.mark.parametrize(
    "invalid_value,field_name",
    [
        ("INVALID_CONTINENT", "continent"),
        ("invalid_role", "producer_role"),
        ("T5_invalid", "trust_tier"),
        ("C6_invalid", "collection_tier"),
    ],
)
def test_no_sources_have_invalid_values(
    sources_config: dict[str, Any], invalid_value: str, field_name: str
) -> None:
    """소스가 잘못된 값을 가지고 있지 않은지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        value = source.get(field_name)

        if isinstance(value, list):
            assert invalid_value not in value, (
                f"{source.get('id')}: {field_name}에 잘못된 값 '{invalid_value}' 포함"
            )
        else:
            assert value != invalid_value, (
                f"{source.get('id')}: {field_name}에 잘못된 값 '{invalid_value}' 설정"
            )
