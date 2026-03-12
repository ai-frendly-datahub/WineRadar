# -*- coding: utf-8 -*-
"""Collector 프로토콜 및 공통 타입 정의."""

from __future__ import annotations

from datetime import datetime
import os
import threading
import time
from typing import Optional, Any, Iterable, Literal, Protocol, TypedDict
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
        self._session = _create_session()
        self._rate_limiters: dict[str, RateLimiter] = {}

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)
        timeout = kwargs.pop("timeout", self._resolve_timeout())
        min_interval = 0.5

        config = self.source_meta.get("config")
        if isinstance(config, dict):
            configured = config.get("request_interval", config.get("min_interval_per_host", 0.5))
            if isinstance(configured, (int, float)):
                min_interval = float(configured)

        host = urlparse(url).netloc.lower() or source_name
        limiter = self._rate_limiters.setdefault(host, RateLimiter(min_interval))

        def _request_impl() -> requests.Response:
            limiter.acquire()
            if method.upper() == "POST":
                response = requests.post(url, timeout=timeout, **kwargs)
            else:
                response = requests.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response

        return breaker.call(
            lambda source=source_name: _request_impl(),
            source=source_name,
        )

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
        return self._request("GET", url)

    def _fetch_html(self, url: str) -> Optional[str]:
        response = self._request("GET", url)
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def _fetch_json(self, url: str) -> dict[str, Any] | list[Any]:
        response = self._request("GET", url)
        return response.json()


class RateLimiter:
    def __init__(self, min_interval: float = 0.5):
        self._min_interval = min_interval
        self._last_request = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()


def resolve_max_workers(max_workers: Optional[int] = None) -> int:
    if max_workers is None:
        raw_value = os.environ.get("RADAR_MAX_WORKERS", "5")
        try:
            parsed = int(raw_value)
        except ValueError:
            parsed = 5
    else:
        parsed = max_workers

    return max(1, min(parsed, 10))


def _create_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


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
