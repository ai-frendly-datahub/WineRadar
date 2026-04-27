"""Scoring 모듈 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from graph.scoring import (
    INFO_PURPOSE_BONUS,
    TRUST_TIER_WEIGHTS,
    calculate_entity_boost,
    calculate_score,
    calculate_time_decay,
)


pytestmark = pytest.mark.unit


def test_trust_tier_weights_defined() -> None:
    """모든 trust_tier에 대한 가중치가 정의되어 있는지 검증."""
    assert "T1_authoritative" in TRUST_TIER_WEIGHTS
    assert "T2_expert" in TRUST_TIER_WEIGHTS
    assert "T3_professional" in TRUST_TIER_WEIGHTS
    assert "T4_community" in TRUST_TIER_WEIGHTS


def test_info_purpose_bonus_defined() -> None:
    """모든 info_purpose에 대한 보너스가 정의되어 있는지 검증."""
    assert "P1_daily_briefing" in INFO_PURPOSE_BONUS
    assert "P2_market_analysis" in INFO_PURPOSE_BONUS
    assert "P3_investment" in INFO_PURPOSE_BONUS
    assert "P4_trend_discovery" in INFO_PURPOSE_BONUS
    assert "P5_education" in INFO_PURPOSE_BONUS


def test_calculate_time_decay_24hours() -> None:
    """24시간 이내: 100% 감쇠 계수."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    recent = now - timedelta(hours=12)

    decay = calculate_time_decay(recent, now)
    assert decay == 1.0


def test_calculate_time_decay_3days() -> None:
    """1-3일: 90% 감쇠 계수."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    two_days_ago = now - timedelta(days=2)

    decay = calculate_time_decay(two_days_ago, now)
    assert decay == 0.9


def test_calculate_time_decay_7days() -> None:
    """3-7일: 70% 감쇠 계수."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    five_days_ago = now - timedelta(days=5)

    decay = calculate_time_decay(five_days_ago, now)
    assert decay == 0.7


def test_calculate_time_decay_14days() -> None:
    """7-14일: 50% 감쇠 계수."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    ten_days_ago = now - timedelta(days=10)

    decay = calculate_time_decay(ten_days_ago, now)
    assert decay == 0.5


def test_calculate_time_decay_30days() -> None:
    """14-30일: 30% 감쇠 계수."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    twenty_days_ago = now - timedelta(days=20)

    decay = calculate_time_decay(twenty_days_ago, now)
    assert decay == 0.3


def test_calculate_time_decay_old() -> None:
    """30일 이상: 10% 감쇠 계수."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    sixty_days_ago = now - timedelta(days=60)

    decay = calculate_time_decay(sixty_days_ago, now)
    assert decay == 0.1


def test_calculate_time_decay_requires_timezone() -> None:
    """timezone-aware datetime 필요."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    naive = datetime(2025, 1, 14, 12, 0, 0, tzinfo=UTC)  # timezone 없음

    with pytest.raises(ValueError, match="timezone-aware"):
        calculate_time_decay(naive, now)


def test_calculate_score_t2_expert_recent() -> None:
    """T2 전문가, 최근 콘텐츠 스코어."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    recent = now - timedelta(hours=1)

    # T2_expert: 2.9, time_decay: 1.0, P1: 1.2
    # 예상: 2.9 * 1.0 * 1.2 = 3.48
    score = calculate_score("T2_expert", ["P1_daily_briefing"], recent, now)
    assert score == 3.48


def test_calculate_score_t1_authoritative_old() -> None:
    """T1 권위, 오래된 콘텐츠 스코어."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    old = now - timedelta(days=7)

    # T1_authoritative: 2.25, time_decay: 0.5, P2: 1.1
    # 예상: 2.25 * 0.5 * 1.1 = 1.2375 -> 1.24
    score = calculate_score("T1_authoritative", ["P2_market_analysis"], old, now)
    assert score == 1.24


def test_calculate_score_multiple_purposes_uses_max() -> None:
    """여러 info_purpose 중 최대 보너스 사용."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    recent = now - timedelta(hours=1)

    # P5_education: 1.0, P1_daily_briefing: 1.2
    # 최대값인 1.2 사용
    score = calculate_score("T3_professional", ["P5_education", "P1_daily_briefing"], recent, now)

    # T3_professional: 2.4, time_decay: 1.0, max_bonus: 1.2
    # 예상: 2.4 * 1.0 * 1.2 = 2.88
    assert score == 2.88


def test_calculate_score_empty_purposes() -> None:
    """info_purpose가 빈 배열인 경우."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    recent = now - timedelta(hours=1)

    # 빈 배열 -> purpose_bonus = 1.0
    score = calculate_score("T4_community", [], recent, now)

    # T4_community: 2.0, time_decay: 1.0, purpose_bonus: 1.0
    # 예상: 2.0 * 1.0 * 1.0 = 2.0
    assert score == 2.0


def test_calculate_score_defaults_to_now() -> None:
    """now 파라미터가 없으면 현재 시각 사용."""
    recent = datetime.now(UTC) - timedelta(hours=1)

    # now=None이면 내부적으로 datetime.now(timezone.utc) 사용
    score = calculate_score("T2_expert", ["P1_daily_briefing"], recent, now=None)

    # 최근이므로 time_decay = 1.0
    # 예상: 2.9 * 1.0 * 1.2 = 3.48
    assert score == 3.48


def test_calculate_entity_boost_no_entities() -> None:
    """엔티티가 없으면 base_score 그대로 반환."""
    score = calculate_entity_boost(3.0, {})
    assert score == 3.0


def test_calculate_entity_boost_single_type() -> None:
    """1개 엔티티 타입: 5% 보너스."""
    score = calculate_entity_boost(3.0, {"winery": ["Château Lafite"]})
    # 3.0 * 1.05 = 3.15
    assert score == 3.15


def test_calculate_entity_boost_two_types() -> None:
    """2개 엔티티 타입: 10% 보너스."""
    score = calculate_entity_boost(3.0, {"winery": ["Lafite"], "wine": ["Bordeaux"]})
    # 3.0 * 1.10 = 3.30
    assert score == 3.3


def test_calculate_entity_boost_max_cap() -> None:
    """5개 이상 엔티티 타입: 25% 최대 보너스."""
    entities = {
        "winery": ["A"],
        "wine": ["B"],
        "grape": ["C"],
        "region": ["D"],
        "topic": ["E"],
        "extra": ["F"],  # 6번째
    }
    score = calculate_entity_boost(4.0, entities)
    # 4.0 * 1.25 = 5.0 (최대 25%)
    assert score == 5.0


@pytest.mark.parametrize(
    "trust_tier,expected_weight",
    [
        ("T1_authoritative", 2.25),
        ("T2_expert", 2.9),
        ("T3_professional", 2.4),
        ("T4_community", 2.0),
    ],
)
def test_trust_tier_weight_mapping(trust_tier: str, expected_weight: float) -> None:
    """trust_tier별 가중치 매핑 검증."""
    assert TRUST_TIER_WEIGHTS[trust_tier] == expected_weight


@pytest.mark.parametrize(
    "age_days,expected_decay",
    [
        (0.5, 1.0),  # 12시간
        (2.0, 0.9),  # 2일
        (5.0, 0.7),  # 5일
        (10.0, 0.5),  # 10일
        (20.0, 0.3),  # 20일
        (60.0, 0.1),  # 60일
    ],
)
def test_time_decay_parameterized(age_days: float, expected_decay: float) -> None:
    """시간 감쇠 함수 파라미터화 테스트."""
    now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    published = now - timedelta(days=age_days)

    decay = calculate_time_decay(published, now)
    assert decay == expected_decay
