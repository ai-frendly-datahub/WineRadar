# -*- coding: utf-8 -*-
"""Collector 프로토콜 및 공통 타입 정의."""

from typing import Protocol, Iterable, TypedDict, Literal
from datetime import datetime

# 메타데이터 타입 정의 (sources.yaml과 일치)
Continent = Literal["OLD_WORLD", "NEW_WORLD", "ASIA"]
ProducerRole = Literal[
    "government",
    "industry_assoc",
    "research_inst",
    "expert_media",
    "trade_media",
    "importer",
    "consumer_comm",
]
TrustTier = Literal[
    "T1_authoritative",
    "T2_expert",
    "T3_professional",
    "T4_community",
]
InfoPurpose = Literal[
    "P1_daily_briefing",
    "P2_market_analysis",
    "P3_investment",
    "P4_trend_discovery",
    "P5_education",
]
CollectionTier = Literal[
    "C1_rss",
    "C2_html_simple",
    "C3_html_js",
    "C4_api",
    "C5_manual",
]


class RawItem(TypedDict):
    """Collector가 수집한 원시 아이템.

    sources.yaml의 사용자 뷰 중심 메타데이터를 포함하여
    Graph Store까지 일관된 분류체계를 적용한다.
    """
    # 콘텐츠 필드
    id: str
    url: str
    title: str
    summary: str | None
    content: str | None
    published_at: datetime
    source_name: str
    source_type: str
    language: str | None
    content_type: str  # news_review, statistics, education, market_report

    # === 사용자 뷰 중심 메타데이터 (sources.yaml과 동일) ===
    # 1. 지리적 메타데이터
    country: str  # ISO 3166-1 alpha-2 (KR, FR, US 등)
    continent: Continent  # OLD_WORLD, NEW_WORLD, ASIA
    region: str  # 계층적 경로 (Europe/Western/France, Asia/East/Korea)

    # 2. 생산자 역할
    producer_role: ProducerRole

    # 3. 신뢰도 등급
    trust_tier: TrustTier

    # 4. 정보 목적 (배열)
    info_purpose: list[InfoPurpose]

    # 5. 수집 난이도
    collection_tier: CollectionTier


class Collector(Protocol):
    source_name: str
    source_type: str

    def collect(self) -> Iterable[RawItem]:
        """해당 소스에서 RawItem 시퀀스를 수집한다.

        - 네트워크/파싱 에러는 내부에서 처리하고,
          문제가 되는 아이템은 건너뛰는 방향으로 설계한다.
        """
        ...
