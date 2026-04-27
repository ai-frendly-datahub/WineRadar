from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import duckdb
import pytest

from mcp_server import server


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


@pytest.mark.unit
def test_search_by_keyword_uses_search_index(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: dict[str, Any] = {}

    class FakeResult:
        def __init__(self, link: str, title: str, snippet: str, rank: float) -> None:
            self.link = link
            self.title = title
            self.snippet = snippet
            self.rank = rank

    class FakeSearchIndex:
        def __init__(self, db_path: Path) -> None:
            calls["db_path"] = db_path

        def __enter__(self) -> FakeSearchIndex:
            return self

        def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
            return None

        def search(self, query: str, *, limit: int = 20) -> list[FakeResult]:
            calls["query"] = query
            calls["limit"] = limit
            return [FakeResult("https://example.com/a", "Bordeaux", "...bordeaux...", -1.0)]

    monkeypatch.setattr(server, "SEARCH_DB_PATH", tmp_path / "search.db", raising=False)
    monkeypatch.setattr(server, "SearchIndex", FakeSearchIndex)

    result = _run(server.handle_search_by_keyword({"keyword": "bordeaux", "limit": 5}))

    assert calls["query"] == "bordeaux"
    assert calls["limit"] == 5
    assert len(result) == 1
    assert "Found 1 items" in result[0].text
    assert "https://example.com/a" in result[0].text


@pytest.mark.unit
def test_call_tool_routes_recent_updates(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_recent(arguments: dict[str, Any]) -> list[Any]:
        assert arguments["limit"] == 1
        return [server.TextContent(type="text", text="ok")]

    monkeypatch.setattr(server, "handle_recent_updates", fake_recent)

    result = _run(server.call_tool("recent_updates", {"limit": 1}))

    assert result[0].text == "ok"


@pytest.mark.unit
def test_call_tool_routes_quality_report(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_quality(arguments: dict[str, Any]) -> list[Any]:
        assert arguments == {}
        return [server.TextContent(type="text", text='{"category": "wine"}')]

    monkeypatch.setattr(server, "handle_quality_report", fake_quality)

    result = _run(server.call_tool("quality_report", {}))

    assert result[0].text == '{"category": "wine"}'


@pytest.mark.unit
def test_list_tools_includes_quality_report() -> None:
    tools = _run(server.list_tools())

    tool_names = {tool.name for tool in tools}
    assert "quality_report" in tool_names


@pytest.mark.unit
def test_sql_tool_rejects_non_select_query() -> None:
    result = _run(server.handle_sql({"query": "DELETE FROM urls"}))

    assert len(result) == 1
    assert "Only SELECT/WITH/EXPLAIN queries are allowed" in result[0].text


@pytest.mark.unit
def test_sql_tool_uses_read_only_connection_and_returns_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = tmp_path / "wineradar.duckdb"
    with duckdb.connect(str(db_path)) as conn:
        conn.execute("CREATE TABLE urls (url TEXT, title TEXT)")
        conn.execute("INSERT INTO urls VALUES ('https://example.com', 'Hello')")

    calls: dict[str, Any] = {}
    real_connect = duckdb.connect

    def wrapped_connect(database: str, read_only: bool = False):
        calls["read_only"] = read_only
        return real_connect(database, read_only=read_only)

    monkeypatch.setattr(server, "DB_PATH", db_path)
    monkeypatch.setattr(server.duckdb, "connect", wrapped_connect)

    result = _run(server.handle_sql({"query": "SELECT url, title FROM urls LIMIT 1"}))

    assert calls["read_only"] is True
    assert "https://example.com" in result[0].text
    assert "Hello" in result[0].text


@pytest.mark.unit
def test_top_trends_counts_entities(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = tmp_path / "wineradar.duckdb"
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE url_entities (
                url TEXT,
                entity_type TEXT,
                entity_value TEXT,
                weight DOUBLE,
                first_seen_at TIMESTAMP,
                last_seen_at TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT INTO url_entities VALUES ('u1', 'grape_variety', 'Merlot', 1.0, now(), now())"
        )
        conn.execute(
            "INSERT INTO url_entities VALUES ('u2', 'grape_variety', 'Merlot', 1.0, now(), now())"
        )
        conn.execute(
            "INSERT INTO url_entities VALUES ('u3', 'region', 'Bordeaux', 1.0, now(), now())"
        )

    monkeypatch.setattr(server, "DB_PATH", db_path)

    result = _run(server.handle_top_trends({"limit": 10}))

    assert "Merlot" in result[0].text
    assert "Bordeaux" in result[0].text
    assert "2" in result[0].text
