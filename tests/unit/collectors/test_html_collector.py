"""HTMLCollector 단위 테스트."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from collectors.html_collector import HTMLCollector

pytestmark = pytest.mark.unit


@pytest.fixture
def wine21_source() -> dict:
    """Wine21 소스 메타데이터."""
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
            "article_selector": ".news-list a",
        },
    }


@pytest.fixture
def sample_list_html() -> bytes:
    """샘플 기사 목록 HTML."""
    return b"""
    <html>
    <body>
        <div class="news-list">
            <a href="/news/article1.html">First Wine Article</a>
            <a href="/news/article2.html">Second Wine Article</a>
            <a href="https://external.com/article3.html">External Article</a>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_article_html() -> bytes:
    """샘플 기사 본문 HTML."""
    return b"""
    <html>
    <body>
        <article>
            <h1>Wine Article Title</h1>
            <div class="date">2025-01-19</div>
            <div class="content">
                <p>This is the article content about wine.</p>
                <p>It contains information about Bordeaux wines.</p>
            </div>
        </article>
    </body>
    </html>
    """


def test_html_collector_initialization(wine21_source: dict) -> None:
    """HTMLCollector 초기화 테스트."""
    collector = HTMLCollector(wine21_source)

    assert collector.source_name == "Wine21"
    assert collector.source_type == "media"
    assert collector.list_url == "https://www.wine21.com/11_news/reporter_news_list.html"


def test_extract_article_list(wine21_source: dict, sample_list_html: bytes) -> None:
    """기사 목록 추출 테스트."""
    def mock_fetcher(url: str) -> bytes:
        return sample_list_html

    collector = HTMLCollector(wine21_source, fetcher=mock_fetcher)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(sample_list_html, "html.parser")
    articles = collector._extract_article_list(soup)

    assert len(articles) >= 2
    assert any("article1.html" in a["url"] for a in articles)
    assert any("First Wine Article" in a["title"] for a in articles)


def test_collect_basic(wine21_source: dict, sample_list_html: bytes) -> None:
    """기본 수집 테스트 (본문 가져오기 없음)."""
    def mock_fetcher(url: str) -> bytes:
        return sample_list_html

    collector = HTMLCollector(wine21_source, fetcher=mock_fetcher)
    items = list(collector.collect())

    assert len(items) >= 2
    assert all(item["source_name"] == "Wine21" for item in items)
    assert all(item["country"] == "KR" for item in items)
    assert all(item["continent"] == "ASIA" for item in items)
    assert all(item["trust_tier"] == "T3_professional" for item in items)


def test_collect_with_content_fetch(wine21_source: dict, sample_list_html: bytes, sample_article_html: bytes) -> None:
    """본문 가져오기 포함 수집 테스트."""
    wine21_source["config"]["fetch_content"] = True
    wine21_source["config"]["content_selector"] = "article"

    fetch_count = {"count": 0}

    def mock_fetcher(url: str) -> bytes:
        fetch_count["count"] += 1
        if "reporter_news_list" in url:
            return sample_list_html
        else:
            return sample_article_html

    collector = HTMLCollector(wine21_source, fetcher=mock_fetcher)
    items = list(collector.collect())

    assert len(items) >= 2
    # 목록 페이지 1회 + 기사 페이지 N회
    assert fetch_count["count"] > 1


def test_extract_article_content(wine21_source: dict, sample_article_html: bytes) -> None:
    """기사 본문 추출 테스트."""
    wine21_source["config"]["content_selector"] = "article"

    def mock_fetcher(url: str) -> bytes:
        return sample_article_html

    collector = HTMLCollector(wine21_source, fetcher=mock_fetcher)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(sample_article_html, "html.parser")
    content = collector._extract_article_content(soup)

    assert content is not None
    assert "Wine Article Title" in content
    assert "Bordeaux wines" in content


def test_parse_date_formats(wine21_source: dict) -> None:
    """날짜 파싱 테스트."""
    collector = HTMLCollector(wine21_source)

    # YYYY-MM-DD 형식
    dt1 = collector._parse_date("2025-01-19")
    assert dt1 is not None
    assert dt1.year == 2025
    assert dt1.month == 1
    assert dt1.day == 19

    # YYYY.MM.DD 형식
    dt2 = collector._parse_date("2025.01.19")
    assert dt2 is not None
    assert dt2.year == 2025

    # YYYY/MM/DD 형식
    dt3 = collector._parse_date("2025/1/19")
    assert dt3 is not None
    assert dt3.year == 2025
    assert dt3.month == 1


def test_parse_date_invalid(wine21_source: dict) -> None:
    """잘못된 날짜 파싱 테스트."""
    collector = HTMLCollector(wine21_source)

    dt = collector._parse_date("invalid date")
    assert dt is None


def test_create_raw_item_structure(wine21_source: dict) -> None:
    """RawItem 구조 검증."""
    collector = HTMLCollector(wine21_source)

    article = {
        "url": "https://www.wine21.com/news/article1.html",
        "title": "Test Wine Article",
    }

    now = datetime.now(timezone.utc)
    item = collector._create_raw_item(article, now)

    assert item is not None
    assert item["url"] == article["url"]
    assert item["title"] == article["title"]
    assert item["source_name"] == "Wine21"
    assert item["country"] == "KR"
    assert item["continent"] == "ASIA"
    assert item["region"] == "Asia/East/Korea"
    assert item["producer_role"] == "trade_media"
    assert item["trust_tier"] == "T3_professional"
    assert "P1_daily_briefing" in item["info_purpose"]
    assert item["collection_tier"] == "C2_html_simple"


def test_collect_handles_errors_gracefully(wine21_source: dict) -> None:
    """에러 처리 테스트."""
    def failing_fetcher(url: str) -> bytes:
        raise Exception("Network error")

    collector = HTMLCollector(wine21_source, fetcher=failing_fetcher)
    items = list(collector.collect())

    # 에러가 발생해도 예외를 던지지 않고 빈 리스트 반환
    assert items == []


def test_article_selector_custom(wine21_source: dict) -> None:
    """커스텀 셀렉터 테스트."""
    wine21_source["config"]["article_selector"] = ".news-item a"

    html = b"""
    <html>
    <body>
        <div class="news-item">
            <a href="/custom1.html">Custom Article 1</a>
        </div>
        <div class="news-item">
            <a href="/custom2.html">Custom Article 2</a>
        </div>
        <a href="/other.html">Other Link</a>
    </body>
    </html>
    """

    def mock_fetcher(url: str) -> bytes:
        return html

    collector = HTMLCollector(wine21_source, fetcher=mock_fetcher)
    items = list(collector.collect())

    assert len(items) == 2
    assert all("custom" in item["url"] for item in items)


def test_missing_article_selector_defaults(wine21_source: dict):
    """article_selector 누락 시 기본값을 사용한다."""
    wine21_source["config"].pop("article_selector", None)

    html = b"<html><body><a href='/sample.html'>Sample</a></body></html>"

    def mock_fetcher(url: str) -> bytes:
        return html

    collector = HTMLCollector(wine21_source, fetcher=mock_fetcher)
    items = list(collector.collect())
    assert len(items) == 1
