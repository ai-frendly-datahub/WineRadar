"""KWCA list pages must yield one absolute article URL per post."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest
import yaml

from collectors.html_collector import HTMLCollector


pytestmark = pytest.mark.unit

FIXTURE = Path("tests/fixtures/kwca_wineinfo_list.html")
LIST_URL = "https://koreawine.or.kr/wineinfo"


def _kwca_source() -> dict[str, Any]:
    config = yaml.safe_load(Path("config/sources.yaml").read_text(encoding="utf-8"))
    source = next(item for item in config["sources"] if item["id"] == "official_koreawine_kr")
    assert source["config"]["list_url"] == LIST_URL
    return source


def test_kwca_fixture_links_each_post_to_its_article() -> None:
    """Fixture saved from the public /wineinfo board. robots.txt allows this path."""
    html = FIXTURE.read_bytes()
    items = list(HTMLCollector(_kwca_source(), fetcher=lambda url: html).collect())

    assert [(item["title"], item["url"]) for item in items] == [
        ("대전 국제와인 expo", "https://koreawine.or.kr/board/view/270/347"),
        (
            "10월 11월 남은 와인 강좌 신청, 롯데백화점 문화센타 비건 와인",
            "https://koreawine.or.kr/board/view/269/347",
        ),
        (
            "외부시음회) 와인 전문인 보르도 그랑크뤼 시음회 신청안내",
            "https://koreawine.or.kr/board/view/268/347",
        ),
    ]
    for item in items:
        parsed = urlparse(item["url"])
        assert parsed.scheme == "https"
        assert parsed.netloc == "koreawine.or.kr"
        assert parsed.path.startswith("/board/view/")
        assert item["url"] != LIST_URL
        assert not item["url"].startswith("/")


def test_kwca_absolute_url_drops_list_page_and_resolves_relative_paths() -> None:
    collector = HTMLCollector(_kwca_source(), fetcher=lambda url: b"")

    assert collector._absolute_article_url("/wineinfo") is None
    assert collector._absolute_article_url("https://koreawine.or.kr/wineinfo/") is None
    assert collector._absolute_article_url("javascript:void(0)") is None
    assert (
        collector._absolute_article_url("board/view/268/347")
        == "https://koreawine.or.kr/board/view/268/347"
    )
