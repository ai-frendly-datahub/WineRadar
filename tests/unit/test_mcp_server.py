# -*- coding: utf-8 -*-
"""MCP 서버 스텁 단위 테스트."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_server.server_stub import (
    load_manifest,
    handle_get_view,
    handle_top_entities,
    main,
)


@pytest.fixture
def manifest_path() -> Path:
    """manifest.json 경로."""
    return Path(__file__).resolve().parent.parent.parent / "mcp_server" / "manifest.json"


class TestLoadManifest:
    """manifest.json 로딩 테스트."""

    def test_load_manifest_returns_dict(self, manifest_path: Path) -> None:
        """manifest.json을 로드하면 dict를 반환한다."""
        manifest = load_manifest(manifest_path)
        assert isinstance(manifest, dict)

    def test_load_manifest_has_required_fields(self, manifest_path: Path) -> None:
        """manifest.json은 name, version, tools를 포함한다."""
        manifest = load_manifest(manifest_path)
        assert "name" in manifest
        assert "version" in manifest
        assert "tools" in manifest
        assert manifest["name"] == "wineradar"

    def test_load_manifest_tools_have_required_fields(self, manifest_path: Path) -> None:
        """각 tool은 name, description, input_schema를 포함한다."""
        manifest = load_manifest(manifest_path)
        tools = manifest["tools"]
        assert len(tools) >= 2

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_load_manifest_contains_get_view_tool(self, manifest_path: Path) -> None:
        """manifest.json은 wineradar.get_view 도구를 포함한다."""
        manifest = load_manifest(manifest_path)
        tool_names = [tool["name"] for tool in manifest["tools"]]
        assert "wineradar.get_view" in tool_names

    def test_load_manifest_contains_top_entities_tool(self, manifest_path: Path) -> None:
        """manifest.json은 wineradar.top_entities 도구를 포함한다."""
        manifest = load_manifest(manifest_path)
        tool_names = [tool["name"] for tool in manifest["tools"]]
        assert "wineradar.top_entities" in tool_names


class TestHandleGetView:
    """get_view 핸들러 테스트."""

    @patch("mcp_server.server_stub.get_view")
    def test_handle_get_view_calls_graph_queries(self, mock_get_view: MagicMock) -> None:
        """handle_get_view는 graph_queries.get_view를 호출한다."""
        mock_get_view.return_value = []

        arguments = {
            "view_type": "winery",
            "focus_id": "test_winery",
            "time_window_days": 7,
            "limit": 20,
        }

        result = handle_get_view(arguments)

        mock_get_view.assert_called_once()
        assert isinstance(result, str)

    @patch("mcp_server.server_stub.get_view")
    def test_handle_get_view_returns_string(self, mock_get_view: MagicMock) -> None:
        """handle_get_view는 문자열을 반환한다."""
        mock_get_view.return_value = []

        arguments = {"view_type": "winery"}

        result = handle_get_view(arguments)

        assert isinstance(result, str)

    @patch("mcp_server.server_stub.get_view")
    def test_handle_get_view_with_empty_results(self, mock_get_view: MagicMock) -> None:
        """결과가 없으면 적절한 메시지를 반환한다."""
        mock_get_view.return_value = []

        arguments = {"view_type": "winery"}

        result = handle_get_view(arguments)

        assert "No items found" in result or "0" in result

    @patch("mcp_server.server_stub.get_view")
    def test_handle_get_view_with_results(self, mock_get_view: MagicMock) -> None:
        """결과가 있으면 항목을 포함한 메시지를 반환한다."""
        mock_item = {
            "url": "https://example.com",
            "title": "Test Wine Article",
            "summary": "Test summary",
            "published_at": "2024-01-01",
            "source_name": "Test Source",
            "source_type": "media",
            "content_type": "news",
            "country": "FR",
            "continent": "EUROPE",
            "region": "Europe/Western/France",
            "producer_role": "winery",
            "trust_tier": "T2",
            "info_purpose": ["P1"],
            "collection_tier": "C1",
            "score": 0.95,
            "entities": {"winery": ["Test Winery"]},
        }
        mock_get_view.return_value = [mock_item]

        arguments = {"view_type": "winery"}

        result = handle_get_view(arguments)

        assert "Test Wine Article" in result or "1" in result

    @patch("mcp_server.server_stub.get_view")
    def test_handle_get_view_with_exception(self, mock_get_view: MagicMock) -> None:
        """예외 발생 시 에러 메시지를 반환한다."""
        mock_get_view.side_effect = Exception("Database error")

        arguments = {"view_type": "winery"}

        result = handle_get_view(arguments)

        assert "Error" in result or "error" in result


class TestHandleTopEntities:
    """top_entities 핸들러 테스트."""

    @patch("mcp_server.server_stub.get_top_entities")
    def test_handle_top_entities_calls_graph_queries(
        self, mock_get_top_entities: MagicMock
    ) -> None:
        """handle_top_entities는 graph_queries.get_top_entities를 호출한다."""
        mock_get_top_entities.return_value = []

        arguments = {
            "entity_type": "winery",
            "time_window_days": 30,
            "limit": 10,
        }

        result = handle_top_entities(arguments)

        mock_get_top_entities.assert_called_once()
        assert isinstance(result, str)

    @patch("mcp_server.server_stub.get_top_entities")
    def test_handle_top_entities_returns_string(self, mock_get_top_entities: MagicMock) -> None:
        """handle_top_entities는 문자열을 반환한다."""
        mock_get_top_entities.return_value = []

        arguments = {"entity_type": "winery"}

        result = handle_top_entities(arguments)

        assert isinstance(result, str)

    @patch("mcp_server.server_stub.get_top_entities")
    def test_handle_top_entities_with_empty_results(self, mock_get_top_entities: MagicMock) -> None:
        """결과가 없으면 적절한 메시지를 반환한다."""
        mock_get_top_entities.return_value = []

        arguments = {"entity_type": "winery"}

        result = handle_top_entities(arguments)

        assert "No entities found" in result or "0" in result

    @patch("mcp_server.server_stub.get_top_entities")
    def test_handle_top_entities_with_results(self, mock_get_top_entities: MagicMock) -> None:
        """결과가 있으면 엔티티를 포함한 메시지를 반환한다."""
        mock_entities = [
            {"entity_type": "winery", "entity_value": "Château Margaux", "count": 15},
            {"entity_type": "winery", "entity_value": "Château Lafite", "count": 12},
        ]
        mock_get_top_entities.return_value = mock_entities

        arguments = {"entity_type": "winery"}

        result = handle_top_entities(arguments)

        assert "Château Margaux" in result or "2" in result

    @patch("mcp_server.server_stub.get_top_entities")
    def test_handle_top_entities_with_exception(self, mock_get_top_entities: MagicMock) -> None:
        """예외 발생 시 에러 메시지를 반환한다."""
        mock_get_top_entities.side_effect = Exception("Database error")

        arguments = {"entity_type": "winery"}

        result = handle_top_entities(arguments)

        assert "Error" in result or "error" in result


class TestMain:
    """main() 함수 테스트."""

    @patch("mcp_server.server_stub.load_manifest")
    def test_main_loads_manifest(self, mock_load_manifest: MagicMock) -> None:
        """main()은 manifest.json을 로드한다."""
        mock_load_manifest.return_value = {
            "name": "wineradar",
            "version": "0.1.0",
            "tools": [],
        }

        main()

        mock_load_manifest.assert_called_once()

    @patch("mcp_server.server_stub.load_manifest")
    def test_main_does_not_raise_exception(self, mock_load_manifest: MagicMock) -> None:
        """main()은 예외를 발생시키지 않는다."""
        mock_load_manifest.return_value = {
            "name": "wineradar",
            "version": "0.1.0",
            "tools": [],
        }

        try:
            main()
        except Exception as e:
            pytest.fail(f"main() raised {type(e).__name__}: {e}")
