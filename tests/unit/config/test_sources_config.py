"""config/sources.yaml 검증."""

from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.unit


def test_sources_entries_have_minimum_fields(sources_config: dict[str, Any]) -> None:
    sources = sources_config.get("sources", [])
    assert sources, "최소 한 개 이상의 source 정의가 필요합니다."

    required_fields = {
        "name",
        "id",
        "type",
        "enabled",
        "weight",
        "config",
    }
    for source in sources:
        assert required_fields <= set(source), f"필수 키 누락: {source}"
        assert isinstance(source["config"], dict), "config는 dict 여야 합니다."


def test_enabled_sources_have_list_url(sources_config: dict[str, Any]) -> None:
    for source in sources_config.get("sources", []):
        if not source.get("enabled", False):
            continue
        list_url = source["config"].get("list_url")
        assert (
            isinstance(list_url, str) and list_url.startswith("https://")
        ), f"list_url 형식 오류: {source['id']}"
