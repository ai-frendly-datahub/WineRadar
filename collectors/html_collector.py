from __future__ import annotations


"""HTML collector for sources that expose structured article lists."""

import logging  # noqa: E402
import random  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
from collections.abc import Callable, Iterable  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from typing import Any  # noqa: E402
from urllib.parse import urljoin  # noqa: E402

import requests  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

from collectors.base import RawItem, validate_raw_item  # noqa: E402


PageFetcher = Callable[[str], bytes]

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
]


class HTMLCollector:
    """Collector implementation dedicated to collection_tier=C2_html_simple."""

    def __init__(self, source_meta: dict[str, Any], fetcher: PageFetcher | None = None):
        self.source_meta = source_meta
        self.source_name = source_meta["name"]
        self.source_type = source_meta["type"]
        self.config = source_meta.get("config", {})

        self.list_url = self.config.get("list_url")
        if not self.list_url:
            raise ValueError("list_url must be provided in config")

        self.article_selector = (
            self.config.get("article_selector") or self.config.get("item_selector") or "a"
        )
        self.link_selector = self.config.get("link_selector")
        self.url_attr = self.config.get("url_attr", "href")
        self.title_selector = self.config.get("title_selector")
        self.summary_selector = self.config.get("summary_selector")
        self.date_selector = self.config.get("date_selector")
        self.max_articles = int(
            self.config.get("max_articles", self.config.get("article_limit", 20))
        )
        self.timeout = float(self.config.get("request_timeout", 10.0))
        self.max_retries = int(self.config.get("max_retries", 3))
        self.backoff_factor = float(self.config.get("retry_backoff", 0.5))
        self.request_interval = float(self.config.get("request_interval", 0.0))
        self.user_agents = self.config.get("user_agents") or DEFAULT_USER_AGENTS
        self.custom_headers = self.config.get("request_headers") or {}
        self.session = requests.Session()
        self._sleep = time.sleep
        self._now = time.monotonic
        self._last_fetch_at: float | None = None

        self.fetcher = fetcher or self._default_fetcher
        self.logger = logging.getLogger(f"{__name__}.{self.source_meta['id']}")

    def _default_fetcher(self, url: str) -> bytes:
        attempt = 0
        last_exc: Exception | None = None

        while attempt < self.max_retries:
            if self.request_interval > 0:
                self._maybe_throttle()
            headers = self._build_headers()
            try:
                response = self.session.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                self._last_fetch_at = self._now()
                return response.content
            except requests.RequestException as exc:
                last_exc = exc
                self.logger.warning("Fetch attempt %s failed for %s: %s", attempt, url, exc)
                attempt += 1
                backoff = self.backoff_factor * (2 ** (attempt - 1))
                if backoff > 0:
                    self._sleep(min(backoff, 5.0))
        raise last_exc or RuntimeError(f"Failed to fetch {url}")

    def _build_headers(self) -> dict[str, str]:
        user_agent = random.choice(self.user_agents)
        headers = {"User-Agent": user_agent}
        headers.update(self.custom_headers)
        return headers

    def _maybe_throttle(self) -> None:
        if self._last_fetch_at is None:
            return
        elapsed = self._now() - self._last_fetch_at
        wait = self.request_interval - elapsed
        if wait > 0:
            self._sleep(wait)

    def collect(self) -> Iterable[RawItem]:
        try:
            list_html = self.fetcher(self.list_url)
            soup = BeautifulSoup(list_html, "html.parser")
            articles = self._extract_article_list(soup)
            if not articles:
                self.logger.warning("No articles extracted from %s", self.list_url)
                return []

            now = datetime.now(UTC)
            for article in articles:
                try:
                    raw_item = self._create_raw_item(article, now)
                    # Validate required fields
                    if raw_item:
                        validation_errors = validate_raw_item(raw_item, self.source_name)
                        if validation_errors:
                            self.logger.warning(
                                "Validation errors for %s: %s",
                                raw_item.get("url"),
                                validation_errors,
                            )
                            continue
                    if raw_item and raw_item["url"]:
                        yield raw_item
                except ValueError as exc:
                    self.logger.warning("Validation error for article %s: %s", article.get("url"), exc)
                    continue
                except KeyError as exc:
                    self.logger.warning("Missing key in article %s: %s", article.get("url"), exc)
                    continue
                except Exception as exc:  # pragma: no cover
                    self.logger.warning("Failed to process article %s: %s", article.get("url"), exc)
                    continue
        except requests.Timeout as exc:
            self.logger.error("Timeout fetching list page %s: %s", self.list_url, exc)
            return []
        except requests.ConnectionError as exc:
            self.logger.error("Connection error fetching list page %s: %s", self.list_url, exc)
            return []
        except requests.HTTPError as exc:
            self.logger.error("HTTP error fetching list page %s: %s", self.list_url, exc)
            return []
        except Exception as exc:
            self.logger.error("Failed to fetch list page %s: %s", self.list_url, exc)
            return []

    def _extract_article_list(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        nodes = soup.select(self.article_selector)

        for node in nodes[: self.max_articles]:
            link_node = node.select_one(self.link_selector) if self.link_selector else node
            if not link_node:
                continue

            href = link_node.get(self.url_attr, "").strip()
            if not href:
                continue

            # Handle JavaScript links (e.g., javascript:goNewsViewDirect(12345))
            if href.startswith("javascript:"):
                # Extract article ID from JavaScript function
                js_match = re.search(r"goNewsViewDirect\((\d+)\)", href)
                if js_match:
                    article_id = js_match.group(1)
                    # Build actual URL based on source
                    if "wine21.com" in self.list_url:
                        href = f"https://www.wine21.com/11_news/news_view.html?news_no={article_id}"
                    else:
                        # Skip unknown JavaScript patterns
                        continue
                else:
                    continue

            if href.startswith("/"):
                href = urljoin(self.list_url, href)
            elif not href.startswith("http"):
                continue

            if self.title_selector:
                title_elem = node.select_one(self.title_selector)
                title = (
                    title_elem.get_text(strip=True)
                    if title_elem
                    else link_node.get_text(strip=True)
                )
            else:
                title = link_node.get_text(strip=True)
            if not title:
                continue

            summary = None
            if self.summary_selector:
                summary_elem = node.select_one(self.summary_selector)
                if summary_elem:
                    summary = summary_elem.get_text(strip=True)

            published_at = None
            if self.date_selector:
                date_elem = node.select_one(self.date_selector)
                date_text = (
                    date_elem.get("datetime")
                    if date_elem and date_elem.has_attr("datetime")
                    else (date_elem.get_text(strip=True) if date_elem else None)
                )
                if date_text:
                    published_at = self._parse_date(date_text)

            articles.append(
                {
                    "url": href,
                    "title": title,
                    "summary": summary,
                    "published_at": published_at,
                }
            )

        return articles

    def _create_raw_item(self, article: dict[str, Any], now: datetime) -> RawItem | None:
        url = article["url"]
        title = article["title"]
        summary = article.get("summary")
        content = article.get("content")
        published_at = article.get("published_at") or now

        if self.config.get("fetch_content", False):
            try:
                article_html = self.fetcher(url)
                article_soup = BeautifulSoup(article_html, "html.parser")
                content = self._extract_article_content(article_soup)
                if not summary:
                    summary = self._extract_summary(article_soup)
                if not article.get("published_at"):
                    date_str = self._extract_published_date(article_soup)
                    if date_str:
                        parsed = self._parse_date(date_str)
                        if parsed:
                            published_at = parsed
            except Exception as exc:  # pragma: no cover
                self.logger.debug("Failed to fetch article body for %s: %s", url, exc)

        raw_item: RawItem = {
            "id": f"{self.source_meta['id']}:{url}",
            "url": url,
            "title": title,
            "summary": summary or self._generate_summary(content, title),
            "content": content,
            "published_at": published_at,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "language": self.source_meta.get("language"),
            "content_type": self.source_meta.get("content_type", "news_review"),
            "country": self.source_meta.get("country", ""),
            "continent": self.source_meta.get("continent", "ASIA"),
            "region": self.source_meta.get("region", ""),
            "producer_role": self.source_meta.get("producer_role", "trade_media"),
            "trust_tier": self.source_meta.get("trust_tier", "T3_professional"),
            "info_purpose": list(self.source_meta.get("info_purpose", [])),
            "collection_tier": self.source_meta.get("collection_tier", "C2_html_simple"),
        }
        return raw_item

    def _extract_article_content(self, soup: BeautifulSoup) -> str | None:
        content_selector = self.config.get("content_selector")
        if not content_selector:
            return None
        content_elem = soup.select_one(content_selector)
        if not content_elem:
            return None
        for tag in content_elem(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        return content_elem.get_text(separator="\n", strip=True)

    def _extract_summary(self, soup: BeautifulSoup) -> str | None:
        summary_selector = self.config.get("detail_summary_selector") or self.summary_selector
        if summary_selector:
            summary_elem = soup.select_one(summary_selector)
            if summary_elem:
                return summary_elem.get_text(strip=True)
        return None

    def _extract_published_date(self, soup: BeautifulSoup) -> str | None:
        date_selector = self.config.get("date_selector")
        if not date_selector:
            return None
        date_elem = soup.select_one(date_selector)
        if date_elem:
            if date_elem.has_attr("datetime"):
                return date_elem.get("datetime")
            return date_elem.get_text(strip=True)
        return None

    def _parse_date(self, date_str: str) -> datetime | None:
        patterns = [
            (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
            (r"(\d{4})\.(\d{1,2})\.(\d{1,2})", "%Y.%m.%d"),
            (r"(\d{4})/(\d{1,2})/(\d{1,2})", "%Y/%m/%d"),
            (
                r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})",
                "%d %b %Y",
            ),
        ]
        for pattern, fmt in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if fmt == "%d %b %Y":
                        day, month_str, year = match.groups()
                        normalized = f"{day} {month_str} {year}"
                        dt = datetime.strptime(normalized, fmt).replace(tzinfo=UTC)
                    else:
                        year, month, day = match.groups()
                        normalized = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        dt = datetime.strptime(normalized, "%Y-%m-%d").replace(tzinfo=UTC)
                    return dt.replace(tzinfo=UTC)
                except ValueError:
                    continue
        return None

    def _generate_summary(self, content: str | None, title: str | None) -> str | None:
        """Fallback summary using content snippet or title."""
        if content:
            normalized = " ".join(content.split())
            if len(normalized) > 280:
                normalized = normalized[:280].rsplit(" ", 1)[0].rstrip() + "…"
            if normalized:
                return normalized
        if title:
            return title.strip()
        return None
