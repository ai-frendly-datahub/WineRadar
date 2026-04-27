"""Collector 프로토콜 및 공통 타입 정의."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Literal, Protocol, TypedDict

import requests

from resilience import SourceCircuitBreakerManager


_DEFAULT_HEALTH_DB_PATH = "data/radar_data.duckdb"


def _load_adaptive_controls() -> tuple[type[Any], type[Any]]:
    module = __import__("radar_core", fromlist=["AdaptiveThrottler", "CrawlHealthStore"])
    return module.AdaptiveThrottler, module.CrawlHealthStore


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
        self.logger = logging.getLogger(f"{__name__}.{self._resolve_source_name()}")
        min_delay = source_meta.get("request_interval", 0.5)
        if not isinstance(min_delay, (int, float)):
            min_delay = 0.5
        throttler_cls, health_store_cls = _load_adaptive_controls()
        self._throttler = throttler_cls(min_delay=max(0.001, float(min_delay)))
        self._health_store = health_store_cls(
            source_meta.get("health_db_path")
            or os.environ.get("RADAR_CRAWL_HEALTH_DB_PATH", _DEFAULT_HEALTH_DB_PATH)
        )

    def _fetch_with_retry(self, url: str, timeout: float) -> requests.Response:
        """Fetch URL with exponential backoff retry.

        Retries on: 408, 429, 500, 502, 503, 504, 522, 524

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            requests.Response object

        Raises:
            requests.Timeout: When request exceeds timeout after retries
            requests.ConnectionError: When connection fails after retries
            requests.HTTPError: When HTTP error persists after retries
        """
        source_name = self._resolve_source_name()
        max_attempts_raw = self.source_meta.get("max_retry_attempts", 3)
        max_attempts = max_attempts_raw if isinstance(max_attempts_raw, int) else 3
        max_attempts = max(1, max_attempts)
        retryable_errors = (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        )

        for attempt in range(max_attempts):
            self._throttler.acquire(source_name)

            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code in (408, 429, 500, 502, 503, 504, 522, 524):
                    self.logger.warning(
                        "Retryable HTTP status %s for %s, will retry",
                        response.status_code,
                        url,
                    )
                    response.raise_for_status()
                response.raise_for_status()

                self._throttler.record_success(source_name)
                delay = self._throttler.get_current_delay(source_name)
                self._health_store.record_success(source_name, delay)
                return response
            except retryable_errors as exc:
                retry_after: int | str | None = None
                if isinstance(exc, requests.exceptions.HTTPError):
                    response = exc.response
                    if response is not None and response.status_code == 429:
                        retry_after = _parse_retry_after(response.headers.get("Retry-After"))

                self._throttler.record_failure(source_name, retry_after=retry_after)
                delay = self._throttler.get_current_delay(source_name)
                self._health_store.record_failure(source_name, str(exc), delay)

                if attempt == max_attempts - 1:
                    raise

        raise RuntimeError("Retry loop exited unexpectedly")

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
        """Fetch URL with timeout and error handling.

        Args:
            url: URL to fetch

        Returns:
            requests.Response object

        Raises:
            requests.Timeout: When request exceeds timeout
            requests.ConnectionError: When connection fails
            requests.HTTPError: When HTTP error status received
        """
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)
        timeout = self._resolve_timeout()

        def _fetch_impl() -> requests.Response:
            try:
                return self._fetch_with_retry(url, timeout)
            except requests.Timeout as exc:
                raise requests.Timeout(f"Request to {url} timed out after {timeout}s") from exc
            except requests.ConnectionError as exc:
                raise requests.ConnectionError(f"Failed to connect to {url}") from exc

        return breaker.call(
            lambda source=source_name: _fetch_impl(),
            source=source_name,
        )

    def _fetch_html(self, url: str) -> str | None:
        """Fetch HTML content from URL with timeout and encoding detection.

        Args:
            url: URL to fetch HTML from

        Returns:
            HTML content as string, or None if failed
        """
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)
        timeout = self._resolve_timeout()

        def _fetch_html_impl() -> str | None:
            try:
                response = self._fetch_with_retry(url, timeout)
                response.encoding = response.apparent_encoding or "utf-8"
                return response.text
            except requests.Timeout as exc:
                raise requests.Timeout(f"HTML fetch from {url} timed out after {timeout}s") from exc
            except requests.ConnectionError as exc:
                raise requests.ConnectionError(f"Failed to fetch HTML from {url}") from exc

        return breaker.call(
            lambda source=source_name: _fetch_html_impl(),
            source=source_name,
        )

    def _fetch_json(self, url: str) -> dict[str, Any] | list[Any]:
        """Fetch JSON data from URL with timeout and error handling.

        Args:
            url: URL to fetch JSON from

        Returns:
            Parsed JSON as dict or list

        Raises:
            requests.Timeout: When request exceeds timeout
            requests.ConnectionError: When connection fails
            ValueError: When JSON parsing fails
        """
        source_name = self._resolve_source_name()
        breaker = self.breaker_manager.get_breaker(source_name)
        timeout = self._resolve_timeout()

        def _fetch_json_impl() -> dict[str, Any] | list[Any]:
            try:
                response = self._fetch_with_retry(url, timeout)
                return response.json()
            except requests.Timeout as exc:
                raise requests.Timeout(f"JSON fetch from {url} timed out after {timeout}s") from exc
            except requests.ConnectionError as exc:
                raise requests.ConnectionError(f"Failed to fetch JSON from {url}") from exc
            except ValueError as exc:
                raise ValueError(f"Failed to parse JSON from {url}") from exc

        return breaker.call(
            lambda source=source_name: _fetch_json_impl(),
            source=source_name,
        )

    def __del__(self) -> None:
        self._health_store.close()


class RawItem(TypedDict):
    """Collector 가 수집한 원시 아이템.

    sources.yaml 의 사용자 뷰 중심 메타데이터를 포함하여
    Graph Store 까지 일관된 분류체계를 적용한다.
    """

    id: str
    url: str
    title: str
    summary: str | None
    content: str | None
    published_at: datetime
    source_name: str
    source_type: str
    language: str | None
    content_type: str

    country: str
    continent: Continent
    region: str
    producer_role: ProducerRole
    trust_tier: TrustTier
    info_purpose: list[InfoPurpose]
    collection_tier: CollectionTier


def validate_raw_item(item: RawItem, source_name: str) -> list[str]:
    """Validate RawItem required fields.

    Args:
        item: RawItem to validate
        source_name: Name of the source for error messages

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []

    # Required fields that must not be empty
    required_fields: list[tuple[str, bool]] = [
        ("id", True),
        ("url", True),
        ("title", True),
        ("published_at", True),
        ("source_name", True),
        ("source_type", True),
        ("content_type", True),
    ]

    for field_name, must_not_be_empty in required_fields:
        value = item.get(field_name)
        if value is None:
            errors.append(f"{source_name}: Missing required field '{field_name}'")
        elif must_not_be_empty and isinstance(value, str) and not value.strip():
            errors.append(f"{source_name}: Empty required field '{field_name}'")

    # Validate URL format
    if item.get("url"):
        url = item["url"]
        if not isinstance(url, str):
            errors.append(f"{source_name}: 'url' must be a string")
        elif not url.startswith("http"):
            errors.append(f"{source_name}: Invalid URL format '{url}'")

    # Validate title length
    if item.get("title"):
        title = item["title"]
        if isinstance(title, str) and len(title.strip()) < 3:
            errors.append(f"{source_name}: Title too short '{title}'")

    return errors


class Collector(Protocol):
    source_name: str
    source_type: str

    def collect(self) -> Iterable[RawItem]:
        """해당 소스에서 RawItem 시퀀스를 수집한다."""
        ...


def _parse_retry_after(value: str | None) -> int | str | None:
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    if stripped.isdigit():
        return int(stripped)

    return stripped
