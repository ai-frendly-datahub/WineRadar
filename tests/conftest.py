"""공통 pytest 픽스처."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml

from collectors.base import RawItem
from graph.graph_queries import ViewItem


@pytest.fixture(scope="session")
def project_root() -> Path:
    """프로젝트 루트 경로."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def sources_config(project_root: Path) -> dict[str, Any]:
    """sources.yaml 전체 로딩."""
    sources_path = project_root / "config" / "sources.yaml"
    with sources_path.open(encoding="utf-8") as fp:
        return yaml.safe_load(fp)


@pytest.fixture()
def sample_raw_item() -> RawItem:
    """Collector가 반환해야 하는 RawItem 예시."""
    published_at = datetime(2024, 1, 1, 12, tzinfo=timezone.utc)
    return RawItem(
        id="sample-item-1",
        url="https://example.com/articles/1",
        title="샘플 와인 기사",
        summary="샘플 요약입니다.",
        content="본문 내용",
        published_at=published_at,
        source_name="Wine21",
        source_type="media",
        language="ko",
    )


@pytest.fixture()
def sample_sections(sample_raw_item: RawItem) -> dict[str, list[ViewItem]]:
    """리포터/뷰 관련 샘플 섹션 데이터."""
    view_item: ViewItem = {
        "url": sample_raw_item["url"],
        "title": sample_raw_item["title"],
        "summary": sample_raw_item["summary"],
        "published_at": sample_raw_item["published_at"],
        "source_name": sample_raw_item["source_name"],
        "source_type": sample_raw_item["source_type"],
        "score": 1.0,
        "entities": {"winery": ["샘플 와이너리"]},
    }
    return {
        "top_issues": [view_item],
        "winery": [view_item],
        "importer": [],
        "community": [],
    }
