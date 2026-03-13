"""Unit tests for HTMLCollector with multilingual fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import requests

from collectors.html_collector import HTMLCollector


pytestmark = pytest.mark.unit


@pytest.fixture
def wine21_source() -> dict:
    """Baseline HTML collector source definition."""
    return {
        "name": "Wine21",
        "id": "media_wine21_kr",
        "type": "media",
        "country": "KR",
        "continent": "ASIA",
        "region": "Asia/East/Korea",
        "producer_role": "trade_media",
        "trust_tier": "T3_professional",
        "info_purpose": ["P1_daily_briefing", "P4_trend_discovery"],
        "collection_tier": "C2_html_simple",
        "content_type": "news_review",
        "language": "ko",
        "config": {
            "list_url": "https://www.wine21.com/11_news/reporter_news_list.html",
            "collection_method": "html",
            "article_selector": "article.news-card",
            "link_selector": "a.news-link",
            "summary_selector": "p.preview",
            "date_selector": "time",
            "content_selector": "article.detail",
            "max_articles": 5,
        },
    }


@pytest.fixture
def sample_list_html() -> bytes:
    return """
    <html>
    <body>
        <article class="news-card">
            <a class="news-link" href="/news/article1.html">첫 번째 기사 제목</a>
            <p class="preview">첫 번째 요약입니다.</p>
            <time datetime="2025-01-19">19 Jan 2025</time>
        </article>
        <article class="news-card">
            <a class="news-link" href="/news/article2.html">Deuxième Vin</a>
            <p class="preview">Résumé français.</p>
            <time>2025/1/20</time>
        </article>
        <article class="news-card">
            <a class="news-link" href="https://external.com/article3.html">External Article</a>
        </article>
    </body>
    </html>
    """.encode()


@pytest.fixture
def latin1_list_html() -> bytes:
    html = """
    <html>
    <head><meta charset="ISO-8859-1"></head>
    <body>
        <article class="news-card">
            <a class="news-link" href="/news/article4.html">Crème de la Crème</a>
            <p class="preview">Résumé détaillé avec accent français.</p>
            <time>2025.01.21</time>
        </article>
    </body>
    </html>
    """
    return html.encode("latin-1")


@pytest.fixture
def sample_article_html() -> bytes:
    return b"""
    <html>
    <body>
        <article class="detail">
            <h1>Wine Article Title</h1>
            <div class="content">
                <p>This is the article content about wine.</p>
                <p>It contains information about Bordeaux wines.</p>
            </div>
        </article>
    </body>
    </html>
    """


def test_extract_article_list(wine21_source: dict, sample_list_html: bytes) -> None:
    collector = HTMLCollector(wine21_source, fetcher=lambda url: sample_list_html)

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(sample_list_html, "html.parser")
    articles = collector._extract_article_list(soup)

    assert len(articles) == 3
    assert articles[0]["summary"] == "첫 번째 요약입니다."
    assert articles[0]["published_at"].year == 2025


def test_collect_basic(wine21_source: dict, sample_list_html: bytes) -> None:
    collector = HTMLCollector(wine21_source, fetcher=lambda url: sample_list_html)
    items = list(collector.collect())

    assert len(items) == 3
    assert items[0]["summary"] == "첫 번째 요약입니다."
    assert items[1]["title"] == "Deuxième Vin"


def test_collect_handles_utf8_and_accents(wine21_source: dict, sample_list_html: bytes) -> None:
    collector = HTMLCollector(wine21_source, fetcher=lambda url: sample_list_html)
    items = list(collector.collect())

    assert any("첫 번째" in (item.get("title") or "") for item in items)
    assert any("Résumé" in (item.get("summary") or "") for item in items)


def test_collect_handles_latin1_encoded_text(wine21_source: dict, latin1_list_html: bytes) -> None:
    collector = HTMLCollector(wine21_source, fetcher=lambda url: latin1_list_html)
    items = list(collector.collect())

    assert len(items) == 1
    assert items[0]["title"].startswith("Crème")
    assert "accent français" in (items[0].get("summary") or "")


def test_collect_with_content_fetch(
    wine21_source: dict, sample_list_html: bytes, sample_article_html: bytes
) -> None:
    wine21_source["config"]["fetch_content"] = True
    fetch_count = {"count": 0}

    def mock_fetcher(url: str) -> bytes:
        fetch_count["count"] += 1
        if "reporter_news_list" in url:
            return sample_list_html
        return sample_article_html

    collector = HTMLCollector(wine21_source, fetcher=mock_fetcher)
    items = list(collector.collect())

    assert len(items) == 3
    assert fetch_count["count"] > 3
    assert items[0]["content"] is not None


def test_extract_article_content(wine21_source: dict, sample_article_html: bytes) -> None:
    collector = HTMLCollector(wine21_source)
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(sample_article_html, "html.parser")
    content = collector._extract_article_content(soup)

    assert "Bordeaux wines" in content


def test_parse_date_formats(wine21_source: dict) -> None:
    collector = HTMLCollector(wine21_source)

    assert collector._parse_date("2025-01-19").year == 2025
    assert collector._parse_date("2025.01.19").month == 1
    assert collector._parse_date("2025/01/19").day == 19
    assert collector._parse_date("19 Jan 2025").day == 19
    assert collector._parse_date("invalid") is None


def test_create_raw_item_structure(wine21_source: dict) -> None:
    collector = HTMLCollector(wine21_source)
    article = {
        "url": "https://www.wine21.com/news/article1.html",
        "title": "Test Wine Article",
        "summary": "짧은 요약",
    }
    now = datetime.now(UTC)
    item = collector._create_raw_item(article, now)

    assert item["summary"] == "짧은 요약"
    assert item["language"] == "ko"


def test_collect_handles_errors_gracefully(wine21_source: dict) -> None:
    def failing_fetcher(url: str) -> bytes:  # type: ignore[return-value]
        raise Exception("boom")

    collector = HTMLCollector(wine21_source, fetcher=failing_fetcher)
    items = list(collector.collect())
    assert items == []


def test_summary_falls_back_to_title_when_missing(wine21_source: dict) -> None:
    collector = HTMLCollector(wine21_source)
    article = {
        "url": "https://example.com/foo",
        "title": "Fallback Title",
        "summary": None,
    }
    now = datetime.now(UTC)
    item = collector._create_raw_item(article, now)
    assert item["summary"] == "Fallback Title"


def test_summary_generated_from_content_when_available(wine21_source: dict) -> None:
    collector = HTMLCollector(wine21_source)
    article = {
        "url": "https://example.com/bar",
        "title": "No Summary",
        "summary": None,
        "content": "첫 문장입니다. 두 번째 문장입니다.",
    }
    now = datetime.now(UTC)
    item = collector._create_raw_item(article, now)
    assert item["summary"].startswith("첫 문장입니다.")


def test_build_headers_respects_configured_user_agent(wine21_source: dict) -> None:
    wine21_source["config"]["user_agents"] = ["CustomAgent/1.0"]
    wine21_source["config"]["request_headers"] = {"X-Test": "1"}
    collector = HTMLCollector(wine21_source)

    headers = collector._build_headers()
    assert headers["User-Agent"] == "CustomAgent/1.0"
    assert headers["X-Test"] == "1"


def test_default_fetcher_retries_then_succeeds(
    monkeypatch: pytest.MonkeyPatch, wine21_source: dict
) -> None:
    wine21_source["config"]["max_retries"] = 2
    wine21_source["config"]["request_interval"] = 0.0
    collector = HTMLCollector(wine21_source)

    collector._now = lambda: 0.5  # type: ignore[assignment]
    sleep_calls: list[float] = []
    collector._sleep = lambda duration: sleep_calls.append(duration)  # type: ignore[assignment]

    class DummyResponse:
        def __init__(self) -> None:
            self.content = b"<html></html>"

        def raise_for_status(self) -> None:
            return None

    call_count = {"count": 0}

    def fake_get(
        url: str, headers: dict | None = None, timeout: float | None = None
    ) -> DummyResponse:
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise requests.HTTPError("boom")
        return DummyResponse()

    collector.session.get = fake_get  # type: ignore[assignment]
    content = collector._default_fetcher("https://example.com")

    assert content.startswith(b"<html>")
    assert call_count["count"] == 2
    assert collector._last_fetch_at == 0.5
    assert sleep_calls  # backoff applied


def test_maybe_throttle_sleeps_when_interval_not_met(wine21_source: dict) -> None:
    collector = HTMLCollector(wine21_source)
    collector.request_interval = 0.2
    collector._last_fetch_at = 0.05  # type: ignore[assignment]
    collector._now = lambda: 0.10  # type: ignore[assignment]
    slept: list[float] = []
    collector._sleep = lambda duration: slept.append(duration)  # type: ignore[assignment]

    collector._maybe_throttle()
    assert slept and pytest.approx(slept[0], rel=0.01) == 0.15
