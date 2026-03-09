"""콘텐츠 스코어링 로직."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Literal

# Trust tier별 가중치 (sources.yaml의 weight 범위 참고)
TRUST_TIER_WEIGHTS = {
    "T1_authoritative": 2.25,  # 2.0-2.5 범위의 중간값
    "T2_expert": 2.9,          # 2.8-3.0 범위의 중간값
    "T3_professional": 2.4,    # 2.0-2.8 범위의 중간값
    "T4_community": 2.0,       # 1.5-2.5 범위의 중간값
}

# Info purpose별 보너스 (사용자 관심도)
INFO_PURPOSE_BONUS = {
    "P1_daily_briefing": 1.2,      # 일일 브리핑 - 높은 관심
    "P2_market_analysis": 1.1,     # 시장 분석 - 중상 관심
    "P3_investment": 1.15,         # 투자 정보 - 중상 관심
    "P4_trend_discovery": 1.1,     # 트렌드 발견 - 중상 관심
    "P5_education": 1.0,           # 교육 - 기본 관심
}

TrustTier = Literal["T1_authoritative", "T2_expert", "T3_professional", "T4_community"]
InfoPurpose = Literal["P1_daily_briefing", "P2_market_analysis", "P3_investment", "P4_trend_discovery", "P5_education"]


def calculate_score(
    trust_tier: TrustTier,
    info_purposes: list[InfoPurpose],
    published_at: datetime,
    now: Optional[datetime] = None,
) -> float:
    """콘텐츠 스코어 계산.

    스코어 = base_weight * time_decay * info_purpose_bonus

    Args:
        trust_tier: 신뢰도 등급 (T1~T4)
        info_purposes: 정보 목적 리스트 (P1~P5)
        published_at: 발행 시각 (timezone-aware datetime)
        now: 현재 시각 (기본값: UTC now)

    Returns:
        float: 계산된 스코어 (0.0 이상)

    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        >>> recent = now - timedelta(hours=1)
        >>> calculate_score("T2_expert", ["P1_daily_briefing"], recent, now)
        3.48  # 2.9 * 1.0 * 1.2

        >>> old = now - timedelta(days=7)
        >>> calculate_score("T2_expert", ["P1_daily_briefing"], old, now)
        1.74  # 2.9 * 0.5 * 1.2 (7일 = 50% 감쇠)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # 1. Base weight (trust_tier 기반)
    base_weight = TRUST_TIER_WEIGHTS.get(trust_tier, 2.0)

    # 2. Time decay (시간 감쇠)
    time_decay = calculate_time_decay(published_at, now)

    # 3. Info purpose bonus (최대값 사용)
    purpose_bonus = 1.0
    if info_purposes:
        purpose_bonuses = [INFO_PURPOSE_BONUS.get(p, 1.0) for p in info_purposes]
        purpose_bonus = max(purpose_bonuses)  # 가장 높은 보너스 적용

    # 최종 스코어
    score = base_weight * time_decay * purpose_bonus
    return round(score, 2)


def calculate_time_decay(published_at: datetime, now: datetime) -> float:
    """시간 감쇠 계산 (최신성 반영).

    감쇠 공식:
    - 0-24시간: 100% (1.0)
    - 1-3일: 90% (0.9)
    - 3-7일: 70% (0.7)
    - 7-14일: 50% (0.5)
    - 14-30일: 30% (0.3)
    - 30일 이상: 10% (0.1)

    Args:
        published_at: 발행 시각
        now: 현재 시각

    Returns:
        float: 시간 감쇠 계수 (0.1 ~ 1.0)
    """
    # Timezone-aware 검증
    if published_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("published_at and now must be timezone-aware")

    age_seconds = (now - published_at).total_seconds()
    age_days = age_seconds / 86400  # 초 -> 일

    if age_days < 1:
        return 1.0
    elif age_days < 3:
        return 0.9
    elif age_days < 7:
        return 0.7
    elif age_days < 14:
        return 0.5
    elif age_days < 30:
        return 0.3
    else:
        return 0.1


def calculate_entity_boost(
    base_score: float,
    matched_entities: dict[str, list[str]],
) -> float:
    """엔티티 매칭 보너스 계산.

    매칭된 엔티티가 많을수록 스코어 상승.

    Args:
        base_score: 기본 스코어
        matched_entities: 매칭된 엔티티 (예: {"winery": ["Château Lafite"], "wine": ["Bordeaux"]})

    Returns:
        float: 보정된 스코어

    Examples:
        >>> calculate_entity_boost(3.0, {"winery": ["Lafite"]})
        3.15  # 3.0 * 1.05 (1개 엔티티 타입)

        >>> calculate_entity_boost(3.0, {"winery": ["Lafite"], "wine": ["Bordeaux"]})
        3.3  # 3.0 * 1.1 (2개 엔티티 타입)
    """
    if not matched_entities:
        return base_score

    # 엔티티 타입 개수에 따라 5%씩 보너스 (최대 25%)
    num_types = len(matched_entities)
    boost_multiplier = 1.0 + min(num_types * 0.05, 0.25)

    return round(base_score * boost_multiplier, 2)
