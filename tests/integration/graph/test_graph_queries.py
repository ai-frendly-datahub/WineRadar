"""graph_queries.get_view 통합 테스트."""

from __future__ import annotations

from datetime import timedelta

import pytest

from graph.graph_queries import get_view

pytestmark = pytest.mark.integration


@pytest.mark.xfail(reason="그래프 쿼리 미구현 상태", strict=False)
def test_get_view_returns_sorted_items():
    """view_type/limit/time_window 요구사항을 캡처한 TDD 가드."""
    window = timedelta(days=7)
    items = get_view("winery", focus_id=None, time_window=window, limit=10)
    assert isinstance(items, list)
    assert len(items) <= 10
