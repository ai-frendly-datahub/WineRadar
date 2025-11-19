# -*- coding: utf-8 -*-
"""Collector 프로토콜 및 공통 타입 정의."""

from typing import Protocol, Iterable, TypedDict
from datetime import datetime


class RawItem(TypedDict):
    id: str
    url: str
    title: str
    summary: str | None
    content: str | None
    published_at: datetime
    source_name: str
    source_type: str
    language: str | None
    # 지리적/분류 메타데이터 (sources.yaml에서 전달됨)
    country: str  # ISO 국가 코드 (KR, FR, US 등)
    continent: str  # OLD_WORLD, NEW_WORLD, ASIA 등
    region: str  # 계층적 지역 (Europe/Western/France)
    tier: str  # official, premium, community
    content_type: str  # news_review, statistics, education, market_report


class Collector(Protocol):
    source_name: str
    source_type: str

    def collect(self) -> Iterable[RawItem]:
        """해당 소스에서 RawItem 시퀀스를 수집한다.

        - 네트워크/파싱 에러는 내부에서 처리하고,
          문제가 되는 아이템은 건너뛰는 방향으로 설계한다.
        """
        ...
