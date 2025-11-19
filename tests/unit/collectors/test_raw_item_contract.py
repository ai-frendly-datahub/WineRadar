"""Collector RawItem 계약 테스트."""

from __future__ import annotations

from datetime import datetime
from typing import get_type_hints

import pytest

from collectors.base import RawItem

pytestmark = pytest.mark.unit


def test_raw_item_contains_all_required_fields(sample_raw_item: RawItem) -> None:
    """RawItem TypedDict 정의와 예시 데이터가 일치하는지 확인."""
    expected_fields = set(get_type_hints(RawItem))
    assert set(sample_raw_item.keys()) == expected_fields
    assert isinstance(sample_raw_item["published_at"], datetime)


def test_raw_item_accepts_nullable_fields(sample_raw_item: RawItem) -> None:
    sample_raw_item["summary"] = None
    sample_raw_item["content"] = None
    sample_raw_item["language"] = None
    # TypedDict 검증용: 값 할당 후에도 dict 형태 유지
    assert "summary" in sample_raw_item and sample_raw_item["summary"] is None
