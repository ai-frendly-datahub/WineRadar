from __future__ import annotations

import json
from pathlib import Path

import pytest

from raw_logger import RawLogger


@pytest.mark.unit
def test_log_raw_items_creates_dated_jsonl_and_writes_lines(tmp_path: Path) -> None:
    logger = RawLogger(tmp_path)
    items = [
        {
            "url": "https://example.com/1",
            "title": "A",
            "source_name": "Wine Source",
            "summary": "first",
            "published_at": "2026-03-04T00:00:00+00:00",
        },
        {
            "url": "https://example.com/2",
            "title": "B",
            "source_name": "Wine Source",
            "summary": "second",
            "published_at": "2026-03-04T01:00:00+00:00",
        },
    ]

    output_path = logger.log_raw_items(items, source_name="Wine Source")

    assert output_path.parent.parent == tmp_path
    assert output_path.parent.name.count("-") == 2
    assert output_path.name == "Wine Source.jsonl"

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["title"] == "A"
    assert json.loads(lines[1])["url"] == "https://example.com/2"


@pytest.mark.unit
def test_log_raw_items_appends_and_preserves_utf8_text(tmp_path: Path) -> None:
    logger = RawLogger(tmp_path)

    output_path = logger.log_raw_items(
        [
            {
                "url": "https://example.com/1",
                "title": "첫 기사",
                "source_name": "KR/Source",
                "summary": "한글 요약",
                "published_at": None,
            }
        ],
        source_name="KR/Source",
    )
    _ = logger.log_raw_items(
        [
            {
                "url": "https://example.com/2",
                "title": "둘째 기사",
                "source_name": "KR/Source",
                "summary": "두번째",
                "published_at": None,
            }
        ],
        source_name="KR/Source",
    )

    assert output_path.name == "KR_Source.jsonl"
    content = output_path.read_text(encoding="utf-8")
    assert "한글 요약" in content
    assert "\\u" not in content
    assert len(content.splitlines()) == 2
