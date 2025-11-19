"""DuckDB 데이터 품질 점검 스크립트."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import duckdb

NULL_CONDITIONS: dict[str, str] = {
    "title": "title IS NULL OR length(trim(title)) = 0",
    "summary": "summary IS NULL OR length(trim(summary)) = 0",
    "content": "content IS NULL OR length(trim(content)) = 0",
    "published_at": "published_at IS NULL",
    "language": "language IS NULL OR length(trim(language)) = 0",
    "region": "region IS NULL OR length(trim(region)) = 0",
    "producer_role": "producer_role IS NULL OR length(trim(producer_role)) = 0",
    "info_purpose": "info_purpose IS NULL OR json_array_length(info_purpose) = 0",
    "source_name": "source_name IS NULL OR length(trim(source_name)) = 0",
}

ALLOWED_LANGUAGES = {"en", "fr", "it", "ko", "ja", "es", "de"}


def _print_section(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def _fetch_rows(con: duckdb.DuckDBPyConnection, query: str) -> Iterable[tuple]:
    return con.execute(query).fetchall()


def check_missing_fields(con: duckdb.DuckDBPyConnection) -> None:
    _print_section("누락 필드 점검")
    total = con.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
    if total == 0:
        print("데이터가 비어 있습니다.")
        return

    for field, condition in NULL_CONDITIONS.items():
        count = con.execute(f"SELECT COUNT(*) FROM urls WHERE {condition}").fetchone()[0]
        ratio = (count / total) * 100 if total else 0
        if count:
            print(f"- {field}: {count} rows ({ratio:.2f}%) 누락/공백")


def check_duplicate_urls(con: duckdb.DuckDBPyConnection, limit: int = 10) -> None:
    _print_section("중복 URL 점검")
    rows = _fetch_rows(
        con,
        f"""
        SELECT url, COUNT(*) AS cnt
        FROM urls
        GROUP BY url
        HAVING cnt > 1
        ORDER BY cnt DESC, url
        LIMIT {limit}
        """,
    )
    if not rows:
        print("중복 URL 없음")
        return
    for url, cnt in rows:
        print(f"- {cnt}회: {url}")


def check_text_lengths(con: duckdb.DuckDBPyConnection) -> None:
    _print_section("텍스트 길이 통계")
    rows = con.execute(
        """
        SELECT
            AVG(length(title)) AS avg_title,
            MIN(length(title)) AS min_title,
            MAX(length(title)) AS max_title,
            AVG(length(summary)) AS avg_summary,
            AVG(length(content)) AS avg_content
        FROM urls
        """
    ).fetchone()
    print(
        f"제목 길이 avg/min/max: {rows[0]:.1f} / {rows[1]} / {rows[2]}\n"
        f"요약 평균 길이: {rows[3]:.1f}\n"
        f"본문 평균 길이: {rows[4]:.1f}"
    )


def check_language_values(con: duckdb.DuckDBPyConnection) -> None:
    _print_section("언어 코드 검증")
    rows = _fetch_rows(
        con,
        """
        SELECT language, COUNT(*) AS cnt
        FROM urls
        GROUP BY language
        ORDER BY cnt DESC
        """,
    )
    invalid = [(lang, cnt) for lang, cnt in rows if lang not in ALLOWED_LANGUAGES]
    if invalid:
        print("허용되지 않은 언어 코드:")
        for lang, cnt in invalid:
            print(f"- {lang}: {cnt}")
    else:
        print("모든 언어 코드가 허용 범위 내에 있습니다.")


def check_dates(con: duckdb.DuckDBPyConnection) -> None:
    _print_section("발행일 점검")
    future_count = con.execute(
        "SELECT COUNT(*) FROM urls WHERE published_at > now()"
    ).fetchone()[0]
    oldest, newest = con.execute(
        "SELECT MIN(published_at), MAX(published_at) FROM urls"
    ).fetchone()
    print(f"가장 오래된 발행일: {oldest}, 최신 발행일: {newest}")
    if future_count:
        print(f"미래 날짜 {future_count}건 존재")


def main() -> None:
    parser = argparse.ArgumentParser(description="DuckDB 데이터 품질 점검")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/test_selected.duckdb"),
        help="검사할 DuckDB 경로",
    )
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"DB 파일이 존재하지 않습니다: {args.db}")

    con = duckdb.connect(str(args.db))
    total = con.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
    print(f"총 레코드 수: {total}")

    check_missing_fields(con)
    check_duplicate_urls(con)
    check_text_lengths(con)
    check_language_values(con)
    check_dates(con)


if __name__ == "__main__":
    main()
