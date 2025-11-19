"""sources.yaml 사용자 뷰 중심 메타데이터 검증 테스트."""

from __future__ import annotations

from typing import Any, Literal

import pytest

pytestmark = pytest.mark.unit

# 허용된 값 정의
VALID_CONTINENTS = {"OLD_WORLD", "NEW_WORLD", "ASIA"}
VALID_PRODUCER_ROLES = {
    "government",
    "industry_assoc",
    "research_inst",
    "expert_media",
    "trade_media",
    "importer",
    "consumer_comm",
}
VALID_TRUST_TIERS = {
    "T1_authoritative",
    "T2_expert",
    "T3_professional",
    "T4_community",
}
VALID_INFO_PURPOSES = {
    "P1_daily_briefing",
    "P2_market_analysis",
    "P3_investment",
    "P4_trend_discovery",
    "P5_education",
}
VALID_COLLECTION_TIERS = {
    "C1_rss",
    "C2_html_simple",
    "C3_html_js",
    "C4_api",
    "C5_manual",
}


def test_all_sources_have_metadata_fields(sources_config: dict[str, Any]) -> None:
    """모든 소스가 사용자 뷰 중심 메타데이터 필드를 가지고 있는지 검증."""
    sources = sources_config.get("sources", [])
    assert sources, "최소 한 개 이상의 source 정의가 필요합니다."

    required_metadata = {
        "country",
        "continent",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
    }

    for source in sources:
        source_id = source.get("id", "unknown")
        missing = required_metadata - set(source.keys())
        assert not missing, f"{source_id}: 필수 메타데이터 필드 누락 - {missing}"


def test_continent_values_are_valid(sources_config: dict[str, Any]) -> None:
    """continent 필드가 허용된 값만 사용하는지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        continent = source.get("continent")
        assert continent in VALID_CONTINENTS, (
            f"{source_id}: 잘못된 continent 값 '{continent}'. "
            f"허용: {VALID_CONTINENTS}"
        )


def test_country_is_iso_alpha2(sources_config: dict[str, Any]) -> None:
    """country 필드가 ISO 3166-1 alpha-2 형식인지 검증 (길이 2)."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        country = source.get("country", "")
        assert isinstance(country, str) and len(country) == 2, (
            f"{source_id}: country는 2글자 ISO alpha-2 코드여야 함 (현재: '{country}')"
        )
        assert country.isupper(), (
            f"{source_id}: country는 대문자여야 함 (현재: '{country}')"
        )


def test_region_is_hierarchical_path(sources_config: dict[str, Any]) -> None:
    """region 필드가 '/' 구분 계층 경로인지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        region = source.get("region", "")
        assert isinstance(region, str) and "/" in region, (
            f"{source_id}: region은 '/' 구분 계층 경로여야 함 (예: 'Europe/Western/France'). "
            f"현재: '{region}'"
        )


def test_producer_role_values_are_valid(sources_config: dict[str, Any]) -> None:
    """producer_role 필드가 허용된 값만 사용하는지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        producer_role = source.get("producer_role")
        assert producer_role in VALID_PRODUCER_ROLES, (
            f"{source_id}: 잘못된 producer_role 값 '{producer_role}'. "
            f"허용: {VALID_PRODUCER_ROLES}"
        )


def test_trust_tier_values_are_valid(sources_config: dict[str, Any]) -> None:
    """trust_tier 필드가 허용된 값만 사용하는지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        trust_tier = source.get("trust_tier")
        assert trust_tier in VALID_TRUST_TIERS, (
            f"{source_id}: 잘못된 trust_tier 값 '{trust_tier}'. "
            f"허용: {VALID_TRUST_TIERS}"
        )


def test_info_purpose_is_array_with_valid_values(sources_config: dict[str, Any]) -> None:
    """info_purpose 필드가 배열이고 허용된 값만 포함하는지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        info_purpose = source.get("info_purpose")

        # 배열 타입 검증
        assert isinstance(info_purpose, list), (
            f"{source_id}: info_purpose는 배열이어야 함 (현재: {type(info_purpose)})"
        )

        # 최소 1개 이상
        assert len(info_purpose) >= 1, (
            f"{source_id}: info_purpose는 최소 1개 이상의 값을 가져야 함"
        )

        # 각 값이 허용된 값인지 검증
        for purpose in info_purpose:
            assert purpose in VALID_INFO_PURPOSES, (
                f"{source_id}: 잘못된 info_purpose 값 '{purpose}'. "
                f"허용: {VALID_INFO_PURPOSES}"
            )


def test_collection_tier_values_are_valid(sources_config: dict[str, Any]) -> None:
    """collection_tier 필드가 허용된 값만 사용하는지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        collection_tier = source.get("collection_tier")
        assert collection_tier in VALID_COLLECTION_TIERS, (
            f"{source_id}: 잘못된 collection_tier 값 '{collection_tier}'. "
            f"허용: {VALID_COLLECTION_TIERS}"
        )


def test_producer_role_trust_tier_consistency(sources_config: dict[str, Any]) -> None:
    """producer_role과 trust_tier의 조합이 일관성 있는지 검증."""
    sources = sources_config.get("sources", [])

    # producer_role → 허용된 trust_tier 매핑
    expected_tier_by_role = {
        "government": ["T1_authoritative"],
        "industry_assoc": ["T1_authoritative"],
        "research_inst": ["T1_authoritative"],
        "expert_media": ["T2_expert"],
        "trade_media": ["T3_professional"],
        "importer": ["T3_professional"],
        "consumer_comm": ["T4_community"],
    }

    for source in sources:
        source_id = source.get("id", "unknown")
        producer_role = source.get("producer_role")
        trust_tier = source.get("trust_tier")

        expected_tiers = expected_tier_by_role.get(producer_role, [])
        assert trust_tier in expected_tiers, (
            f"{source_id}: producer_role '{producer_role}'에 대해 "
            f"trust_tier '{trust_tier}'는 부적절함. "
            f"예상: {expected_tiers}"
        )


def test_enabled_sources_have_collection_method(sources_config: dict[str, Any]) -> None:
    """enabled=true인 소스는 config.collection_method를 가져야 함."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        enabled = source.get("enabled", False)

        if enabled:
            config = source.get("config", {})
            collection_method = config.get("collection_method")
            assert collection_method in {"rss", "html", "api"}, (
                f"{source_id}: enabled=true이지만 collection_method가 누락되거나 잘못됨. "
                f"현재: '{collection_method}'"
            )


def test_rss_sources_have_c1_collection_tier(sources_config: dict[str, Any]) -> None:
    """collection_method=rss인 소스는 collection_tier=C1_rss여야 함."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        config = source.get("config", {})
        collection_method = config.get("collection_method")

        if collection_method == "rss":
            collection_tier = source.get("collection_tier")
            assert collection_tier == "C1_rss", (
                f"{source_id}: collection_method='rss'이지만 "
                f"collection_tier='{collection_tier}' (C1_rss여야 함)"
            )


def test_continent_country_region_consistency(sources_config: dict[str, Any]) -> None:
    """continent, country, region의 일관성 검증."""
    sources = sources_config.get("sources", [])

    # continent → 예상 region prefix 매핑
    expected_region_prefix = {
        "OLD_WORLD": ["Europe/", "Africa/North", "Africa/East", "Middle East/"],
        "NEW_WORLD": ["Americas/", "Oceania/", "Africa/South"],  # South Africa는 NEW_WORLD
        "ASIA": ["Asia/"],
    }

    for source in sources:
        source_id = source.get("id", "unknown")
        continent = source.get("continent")
        region = source.get("region", "")

        expected_prefixes = expected_region_prefix.get(continent, [])
        has_valid_prefix = any(region.startswith(prefix) for prefix in expected_prefixes)

        assert has_valid_prefix, (
            f"{source_id}: continent '{continent}'와 region '{region}'이 일치하지 않음. "
            f"region은 다음 중 하나로 시작해야 함: {expected_prefixes}"
        )


def test_phase1_sources_are_enabled(sources_config: dict[str, Any]) -> None:
    """Phase 1 소스 (Decanter, Gambero Rosso)는 enabled=true여야 함."""
    sources = sources_config.get("sources", [])

    phase1_sources = {
        "media_decanter_global",
        "media_gambero_it",
    }

    for source in sources:
        source_id = source.get("id", "unknown")
        if source_id in phase1_sources:
            enabled = source.get("enabled", False)
            assert enabled, (
                f"{source_id}: Phase 1 소스이므로 enabled=true여야 함 (현재: {enabled})"
            )

            # RSS 피드 확인
            collection_tier = source.get("collection_tier")
            assert collection_tier == "C1_rss", (
                f"{source_id}: Phase 1 소스는 C1_rss여야 함 (현재: {collection_tier})"
            )


def test_source_id_naming_convention(sources_config: dict[str, Any]) -> None:
    """source id가 '{type}_{name}_{country}' 형식인지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "")
        parts = source_id.split("_")

        assert len(parts) >= 3, (
            f"{source_id}: id는 최소 3개 부분으로 구성되어야 함 "
            f"(형식: type_name_country). 현재: {len(parts)} parts"
        )

        # 마지막 부분이 country 코드인지 확인 (소문자 2글자 또는 "global")
        country_code = parts[-1]
        is_valid_country = len(country_code) == 2 and country_code.islower()
        is_global_source = country_code == "global"

        assert is_valid_country or is_global_source, (
            f"{source_id}: id의 마지막 부분은 소문자 2글자 국가 코드 또는 'global'이어야 함 "
            f"(현재: '{country_code}')"
        )


def test_info_purpose_time_window_consistency(sources_config: dict[str, Any]) -> None:
    """info_purpose와 content_type의 일관성 검증."""
    sources = sources_config.get("sources", [])

    # P1 (daily_briefing) → news_review
    # P2 (market_analysis) → statistics, market_report
    # P5 (education) → education, statistics (연구기관은 통계 자료로 교육 가능)
    purpose_content_map = {
        "P1_daily_briefing": ["news_review"],
        "P2_market_analysis": ["statistics", "market_report"],
        "P3_investment": ["news_review", "expert_rating"],
        "P4_trend_discovery": ["news_review"],
        "P5_education": ["education", "statistics"],  # statistics도 교육 목적 제공 가능
    }

    for source in sources:
        source_id = source.get("id", "unknown")
        info_purpose = source.get("info_purpose", [])
        content_type = source.get("content_type", "")

        for purpose in info_purpose:
            expected_types = purpose_content_map.get(purpose, [])
            if expected_types:  # 매핑이 정의된 경우만 검증
                assert content_type in expected_types, (
                    f"{source_id}: info_purpose '{purpose}'에 대해 "
                    f"content_type '{content_type}'는 부적절함. "
                    f"예상: {expected_types}"
                )


def test_all_sources_have_unique_ids(sources_config: dict[str, Any]) -> None:
    """모든 소스의 id가 중복되지 않는지 검증."""
    sources = sources_config.get("sources", [])

    ids = [source.get("id") for source in sources]
    unique_ids = set(ids)

    assert len(ids) == len(unique_ids), (
        f"중복된 source id 발견. 전체: {len(ids)}, 고유: {len(unique_ids)}"
    )


def test_metadata_field_types(sources_config: dict[str, Any]) -> None:
    """메타데이터 필드의 타입이 올바른지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")

        # 문자열 필드
        for field in ["country", "continent", "region", "producer_role", "trust_tier", "collection_tier"]:
            value = source.get(field)
            assert isinstance(value, str), (
                f"{source_id}: {field}는 문자열이어야 함 (현재: {type(value)})"
            )

        # 배열 필드
        info_purpose = source.get("info_purpose")
        assert isinstance(info_purpose, list), (
            f"{source_id}: info_purpose는 배열이어야 함 (현재: {type(info_purpose)})"
        )

        # 불리언 필드
        enabled = source.get("enabled")
        assert isinstance(enabled, bool), (
            f"{source_id}: enabled는 불리언이어야 함 (현재: {type(enabled)})"
        )

        # 숫자 필드
        weight = source.get("weight")
        assert isinstance(weight, (int, float)), (
            f"{source_id}: weight는 숫자여야 함 (현재: {type(weight)})"
        )


def test_weight_range(sources_config: dict[str, Any]) -> None:
    """weight 값이 허용 범위 (1.0 ~ 3.0) 내인지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        weight = source.get("weight", 0)

        assert 1.0 <= weight <= 3.0, (
            f"{source_id}: weight는 1.0 ~ 3.0 범위여야 함 (현재: {weight})"
        )


def test_trust_tier_weight_consistency(sources_config: dict[str, Any]) -> None:
    """trust_tier에 따른 weight 범위가 적절한지 검증."""
    sources = sources_config.get("sources", [])

    # trust_tier → 예상 weight 범위
    expected_weight_range = {
        "T1_authoritative": (2.0, 2.5),  # 공식 기관
        "T2_expert": (2.8, 3.0),  # 전문가 미디어
        "T3_professional": (2.0, 2.8),  # 업계 전문가
        "T4_community": (1.5, 2.5),  # 커뮤니티
    }

    for source in sources:
        source_id = source.get("id", "unknown")
        trust_tier = source.get("trust_tier")
        weight = source.get("weight", 0)

        min_weight, max_weight = expected_weight_range.get(trust_tier, (1.0, 3.0))

        assert min_weight <= weight <= max_weight, (
            f"{source_id}: trust_tier '{trust_tier}'에 대해 "
            f"weight {weight}는 범위를 벗어남. "
            f"예상 범위: {min_weight} ~ {max_weight}"
        )


def test_sources_include_multiple_languages(sources_config: dict[str, Any]) -> None:
    sources = sources_config.get("sources", [])
    languages = {src.get("language") for src in sources if src.get("enabled") and src.get("language")}

    required = {
        "ko": "한국어 소스가 활성화되어야 합니다.",
        "en": "영어 소스가 활성화되어야 합니다.",
        "fr": "프랑스어 소스가 활성화되어야 합니다.",
        "it": "이탈리아어 소스가 활성화되어야 합니다.",
    }

    for lang, message in required.items():
        assert lang in languages, message


def test_all_sources_define_language_field(sources_config: dict[str, Any]) -> None:
    """language 필드가 누락되지 않고 ISO 소문자 형식을 따르는지 검증."""
    sources = sources_config.get("sources", [])

    for source in sources:
        source_id = source.get("id", "unknown")
        language = source.get("language")
        assert isinstance(language, str) and language, f"{source_id}: language 필드가 누락되었거나 비어 있음"

        normalized = language.replace("-", "")
        assert normalized.isalpha(), f"{source_id}: language '{language}'는 알파벳 이어야 함"
        assert language == language.lower(), f"{source_id}: language '{language}'는 소문자 형식을 사용해야 함"
        assert len(language.split("-")[0]) == 2, f"{source_id}: language '{language}'는 ISO 639-1 코드여야 함"


