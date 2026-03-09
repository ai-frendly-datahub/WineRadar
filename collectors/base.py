# -*- coding: utf-8 -*-
"""Collector 프로토콜 및 공통 타입 정의."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any, Iterable, Literal, Protocol, TypedDict

import requests

from resilience import SourceCircuitBreakerManager

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


class BaseCollector:
    def __init__(self, source_meta: dict[str, Any]) -> None:
        self.source_meta = source_meta
        self.breaker_manager = SourceCircuitBreakerManager()

    def _resolve_source_name(self) -> str:
        source_name = self.source_meta.get("name")
        if isinstance(source_name, str) and source_name:
            return source_name

        source_id = self.source_meta.get("id")
        if isinstance(source_id, str) and source_id:
            return source_id

        return "unknown_source"

    def _resolve_timeout(self) -> float:
        config = self.source_meta.get("config")
        if not isinstance(config, dict):
            return 10.0

        timeout = config.get("request_timeout", config.get("timeout", 10.0))
        if isinstance(timeout, (int, float)):
            return float(timeout)
        return 10.0

    def _fetch(self, url: str) -> requests.Response:
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)

        def _fetch_impl() -> requests.Response:
            response = requests.get(url, timeout=self._resolve_timeout())
            response.raise_for_status()
            return response

        return breaker.call(
            lambda source=source_name: _fetch_impl(),
            source=source_name,
        )

    def _fetch_html(self, url: str) -> Optional[str]:
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)

        def _fetch_html_impl() -> Optional[str]:
            response = requests.get(url, timeout=self._resolve_timeout())
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            return response.text

        return breaker.call(
            lambda source=source_name: _fetch_html_impl(),
            source=source_name,
        )

    def _fetch_json(self, url: str) -> dict[str, Any] | list[Any]:
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)

        def _fetch_json_impl() -> dict[str, Any] | list[Any]:
            response = requests.get(url, timeout=self._resolve_timeout())
            response.raise_for_status()
            return response.json()

        return breaker.call(
            lambda source=source_name: _fetch_json_impl(),
            source=source_name,
        )


class RawItem(TypedDict):
    """Collector가 수집한 원시 아이템.

    sources.yaml의 사용자 뷰 중심 메타데이터를 포함하여
    Graph Store까지 일관된 분류체계를 적용한다.
    """

    id: str
    url: str
    title: str
    summary: Optional[str]
    content: Optional[str]
    published_at: datetime
    source_name: str
    source_type: str
    language: Optional[str]
    content_type: str

    country: str
    continent: Continent
    region: str
    producer_role: ProducerRole
    trust_tier: TrustTier
    info_purpose: list[InfoPurpose]
    collection_tier: CollectionTier


class Collector(Protocol):
    source_name: str
    source_type: str

    def collect(self) -> Iterable[RawItem]:
        """해당 소스에서 RawItem 시퀀스를 수집한다."""
        ...
