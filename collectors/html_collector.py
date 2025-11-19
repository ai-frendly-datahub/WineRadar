"""HTML 기반 Collector 구현."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Callable, Iterable, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from collectors.base import RawItem


PageFetcher = Callable[[str], bytes]


class HTMLCollector:
    """collection_tier=C2_html_simple 소스를 위한 범용 Collector."""

    def __init__(self, source_meta: dict[str, Any], fetcher: PageFetcher | None = None):
        self.source_meta = source_meta
        self.source_name = source_meta["name"]
        self.source_type = source_meta["type"]
        self.config = source_meta.get("config", {})
        self.list_url = self.config.get("list_url")
        if not self.list_url:
            raise ValueError("list_url must be provided in config")
        self.logger = logging.getLogger(f"{__name__}.{self.source_meta['id']}")
        self.article_selector = self.config.get("article_selector")
        if not self.article_selector:
            self.logger.warning("article_selector not set for %s, defaulting to 'a'", self.source_meta["id"])
            self.article_selector = "a"

        self.fetcher = fetcher or self._default_fetcher
        self.article_limit = int(self.config.get("article_limit", 20))

    def _default_fetcher(self, url: str) -> bytes:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content

    def collect(self) -> Iterable[RawItem]:
        try:
            list_html = self.fetcher(self.list_url)
            soup = BeautifulSoup(list_html, "html.parser")
            articles = self._extract_article_list(soup)
            if not articles:
                self.logger.warning("No articles extracted from %s", self.list_url)
                return []

            now = datetime.now(timezone.utc)
            for article in articles:
                try:
                    raw_item = self._create_raw_item(article, now)
                    if raw_item and raw_item["url"]:
                        yield raw_item
                except Exception as exc:  # pragma: no cover
                    self.logger.warning("Failed to process article %s: %s", article.get("url"), exc)
                    continue
        except Exception as exc:
            self.logger.error("Failed to fetch list page %s: %s", self.list_url, exc)
            return []

    def _extract_article_list(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        articles: list[dict[str, str]] = []
        links = soup.select(self.article_selector)

        for link in links[: self.article_limit]:
            href = link.get("href", "").strip()
            if not href:
                continue
            if href.startswith("/"):
                href = urljoin(self.list_url, href)
            elif not href.startswith("http"):
                continue

            title = link.get_text(strip=True)
            if not title:
                continue

            articles.append({"url": href, "title": title})
        return articles

    def _create_raw_item(self, article: dict[str, str], now: datetime) -> RawItem | None:
        url = article["url"]
        title = article["title"]
        summary = article.get("summary")
        content = None
        published_at = now

        if self.config.get("fetch_content", False):
            try:
                article_html = self.fetcher(url)
                article_soup = BeautifulSoup(article_html, "html.parser")
                content = self._extract_article_content(article_soup)
                date_str = self._extract_published_date(article_soup)
                if date_str:
                    published_at = self._parse_date(date_str) or now
            except Exception as exc:  # pragma: no cover
                self.logger.debug("Failed to fetch article body for %s: %s", url, exc)

        raw_item: RawItem = {
            "id": f"{self.source_meta['id']}:{url}",
            "url": url,
            "title": title,
            "summary": summary,
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

    def _extract_published_date(self, soup: BeautifulSoup) -> str | None:
        date_selector = self.config.get("date_selector")
        if not date_selector:
            return None
        date_elem = soup.select_one(date_selector)
        if date_elem:
            return date_elem.get_text(strip=True)
        return None

    def _parse_date(self, date_str: str) -> datetime | None:
        patterns = [
            (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
            (r"(\d{4})\.(\d{1,2})\.(\d{1,2})", "%Y.%m.%d"),
            (r"(\d{4})/(\d{1,2})/(\d{1,2})", "%Y/%m/%d"),
        ]
        for pattern, fmt in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    date_only = "-".join(
                        [match.group(1), match.group(2).zfill(2), match.group(3).zfill(2)]
                    )
                    dt = datetime.strptime(date_only, "%Y-%m-%d")
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        return None
