from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from graph.search_index import SearchIndex


@pytest.mark.unit
def test_search_index_creates_tables_and_triggers(tmp_path: Path) -> None:
    db_path = tmp_path / "search_index.db"

    with SearchIndex(db_path):
        pass

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT name, type FROM sqlite_master").fetchall()
    finally:
        conn.close()

    objects = {(str(name), str(object_type)) for name, object_type in rows}
    assert ("documents", "table") in objects
    assert ("documents_fts", "table") in objects
    assert ("documents_ai", "trigger") in objects
    assert ("documents_ad", "trigger") in objects
    assert ("documents_au", "trigger") in objects


@pytest.mark.unit
def test_upsert_and_search_returns_expected_result(tmp_path: Path) -> None:
    index = SearchIndex(tmp_path / "search_index.db")
    index.upsert(
        link="https://example.com/a",
        title="Bordeaux market update",
        body="The bordeaux wine market has shown strong demand.",
    )

    results = index.search("bordeaux")
    index.close()

    assert len(results) == 1
    assert results[0].link == "https://example.com/a"
    assert results[0].title == "Bordeaux market update"
    assert "bordeaux" in results[0].snippet.lower()
    assert isinstance(results[0].rank, float)


@pytest.mark.unit
def test_upsert_same_link_updates_document(tmp_path: Path) -> None:
    index = SearchIndex(tmp_path / "search_index.db")

    index.upsert(link="https://example.com/a", title="Old", body="first version")
    index.upsert(link="https://example.com/a", title="New", body="second version")

    second = index.search("second")
    first = index.search("first")
    index.close()

    assert len(second) == 1
    assert second[0].title == "New"
    assert first == []


@pytest.mark.unit
def test_search_respects_limit_and_returns_empty_for_non_positive_limit(tmp_path: Path) -> None:
    index = SearchIndex(tmp_path / "search_index.db")
    for idx in range(4):
        index.upsert(
            link=f"https://example.com/{idx}",
            title=f"Doc {idx}",
            body="wine market bordeaux",
        )

    limited = index.search("wine", limit=2)
    none = index.search("wine", limit=0)
    index.close()

    assert len(limited) == 2
    assert none == []


@pytest.mark.unit
def test_context_manager_closes_connection(tmp_path: Path) -> None:
    with SearchIndex(tmp_path / "search_index.db") as index:
        index.upsert(link="https://example.com/a", title="A", body="content")
        assert len(index.search("content")) == 1

    with pytest.raises(sqlite3.ProgrammingError):
        _ = index.search("content")
