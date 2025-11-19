#!/usr/bin/env python
"""WineRadar 전체 파이프라인 데모: 데이터 수집 → 그래프 저장 → 다양한 뷰 조회."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import yaml

from collectors.rss_collector import RSSCollector
from collectors.html_collector import HTMLCollector
from analyzers.entity_extractor import extract_all_entities
from graph.graph_store import init_database, upsert_url_and_entities
from graph.graph_queries import get_view


def main() -> None:
    """전체 파이프라인 실행."""
    print("=" * 80)
    print("WineRadar 데이터 수집 및 뷰 생성 데모")
    print("=" * 80)

    # 1. sources.yaml 로드
    print("\n[1단계] sources.yaml 로딩...")
    sources_path = Path("config/sources.yaml")
    with sources_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    sources = config.get("sources", [])
    rss_sources = [
        s for s in sources
        if s.get("enabled") and s.get("collection_tier") == "C1_rss"
    ]
    html_sources = [
        s for s in sources
        if s.get("enabled") and s.get("collection_tier") == "C2_html_simple"
    ]
    print(f"[OK] 활성화된 RSS 소스: {len(rss_sources)}개")
    for source in rss_sources:
        print(f"  - {source['name']} ({source['trust_tier']}, {source['continent']})")
    print(f"[OK] 활성화된 HTML 소스: {len(html_sources)}개")
    for source in html_sources:
        # ASCII-safe 출력
        name_safe = source['name'].encode('ascii', 'ignore').decode('ascii') or source['name']
        print(f"  - {name_safe} ({source['trust_tier']}, {source['continent']})")

    # 2. DuckDB 초기화
    print("\n[2단계] DuckDB 초기화...")
    db_path = Path("data/demo.duckdb")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()  # 기존 DB 삭제
    init_database(db_path)
    print(f"[OK] 데이터베이스 생성: {db_path}")

    # 3. 데이터 수집 및 엔티티 추출
    print("\n[3단계] RSS/HTML 데이터 수집 및 엔티티 추출...")
    now = datetime.now(timezone.utc)
    total_collected = 0
    total_entities = 0

    # 3-1. RSS 소스 수집
    for source in rss_sources[:2]:  # 처음 2개 RSS 소스
        print(f"\n  [RSS] 수집 중: {source['name']}...")
        try:
            collector = RSSCollector(source)
            items = list(collector.collect())

            for item in items[:10]:  # 각 소스에서 최대 10개
                # 엔티티 추출
                entities = extract_all_entities(item)

                # URL 및 엔티티 저장
                upsert_url_and_entities(item, entities, now, db_path)
                total_collected += 1

                # 추출된 엔티티 수 집계
                if entities:
                    entity_count = sum(len(v) for v in entities.values())
                    total_entities += entity_count

            print(f"  [OK] {len(items[:10])}개 아이템 저장 (스코어 자동 계산)")
            print(f"    - trust_tier: {source['trust_tier']}")
            print(f"    - info_purpose: {source['info_purpose']}")

        except Exception as e:
            print(f"  [ERROR] 오류: {e}")

    # 3-2. HTML 소스 수집
    for source in html_sources[:2]:  # 처음 2개 HTML 소스
        print(f"\n  [HTML] 수집 중: {source['name']}...")
        try:
            collector = HTMLCollector(source)
            items = list(collector.collect())

            for item in items[:5]:  # HTML은 속도가 느리므로 5개만
                # 엔티티 추출
                entities = extract_all_entities(item)

                # URL 및 엔티티 저장
                upsert_url_and_entities(item, entities, now, db_path)
                total_collected += 1

                # 추출된 엔티티 수 집계
                if entities:
                    entity_count = sum(len(v) for v in entities.values())
                    total_entities += entity_count

            print(f"  [OK] {len(items[:5])}개 아이템 저장 (스코어 자동 계산)")
            print(f"    - trust_tier: {source['trust_tier']}")
            print(f"    - info_purpose: {source['info_purpose']}")

        except Exception as e:
            print(f"  [ERROR] 오류: {e}")

    print(f"\n[OK] 총 {total_collected}개 아이템 수집 완료")
    print(f"[OK] 총 {total_entities}개 엔티티 추출 완료")

    # 4. 다양한 뷰 조회
    print("\n[4단계] 다양한 관점에서 뷰 조회...")

    # 4-1. 구대륙(OLD_WORLD) 뷰
    print("\n  [뷰 1] 구대륙(OLD_WORLD) 콘텐츠:")
    old_world = get_view(
        db_path=db_path,
        view_type="continent",
        focus_id="OLD_WORLD",
        time_window=timedelta(days=30),
        limit=5,
    )
    print(f"  [OK] {len(old_world)}개 발견")
    for i, item in enumerate(old_world[:3], 1):
        title_safe = item['title'][:60].encode('ascii', 'ignore').decode('ascii')
        print(f"    {i}. [{item['score']:.2f}] {title_safe}...")
        print(f"       {item['source_name']} | {item['country']} | {item['producer_role']}")

    # 4-2. T2 전문가 소스 뷰
    print("\n  [뷰 2] T2 전문가(T2_expert) 소스:")
    expert = get_view(
        db_path=db_path,
        view_type="trust_tier",
        focus_id="T2_expert",
        time_window=timedelta(days=30),
        limit=5,
    )
    print(f"  [OK] {len(expert)}개 발견")
    for i, item in enumerate(expert[:3], 1):
        title_safe = item['title'][:60].encode('ascii', 'ignore').decode('ascii')
        print(f"    {i}. [{item['score']:.2f}] {title_safe}...")
        print(f"       {item['source_name']} | {item['trust_tier']}")

    # 4-3. 일일 브리핑(P1_daily_briefing) 목적 뷰
    print("\n  [뷰 3] 일일 브리핑(P1_daily_briefing) 목적:")
    briefing = get_view(
        db_path=db_path,
        view_type="info_purpose",
        focus_id="P1_daily_briefing",
        time_window=timedelta(days=30),
        limit=5,
    )
    print(f"  [OK] {len(briefing)}개 발견")
    for i, item in enumerate(briefing[:3], 1):
        title_safe = item['title'][:60].encode('ascii', 'ignore').decode('ascii')
        print(f"    {i}. [{item['score']:.2f}] {title_safe}...")
        print(f"       {item['source_name']} | {item['info_purpose']}")

    # 4-4. 특정 국가(GB - 영국) 뷰
    print("\n  [뷰 4] 영국(GB) 소스:")
    uk = get_view(
        db_path=db_path,
        view_type="country",
        focus_id="GB",
        time_window=timedelta(days=30),
        limit=5,
    )
    print(f"  [OK] {len(uk)}개 발견")
    for i, item in enumerate(uk[:3], 1):
        title_safe = item['title'][:60].encode('ascii', 'ignore').decode('ascii')
        print(f"    {i}. [{item['score']:.2f}] {title_safe}...")
        print(f"       {item['source_name']} | {item['region']}")

    # 4-5. 엔티티 기반 뷰 (포도 품종)
    print("\n  [뷰 5] 포도 품종(Cabernet Sauvignon) 엔티티:")
    grape_items = get_view(
        db_path=db_path,
        view_type="grape_variety",
        focus_id="Cabernet Sauvignon",
        time_window=timedelta(days=30),
        limit=5,
    )
    print(f"  [OK] {len(grape_items)}개 발견")
    for i, item in enumerate(grape_items[:3], 1):
        title_safe = item['title'][:60].encode('ascii', 'ignore').decode('ascii')
        print(f"    {i}. [{item['score']:.2f}] {title_safe}...")
        print(f"       {item['source_name']} | 엔티티 보너스 적용")

    # 5. 통계 요약
    print("\n" + "=" * 80)
    print("데모 완료!")
    print("=" * 80)
    print(f"\n[OK] 수집된 아이템: {total_collected}개")
    print(f"[OK] 추출된 엔티티: {total_entities}개")
    print(f"[OK] 구대륙 콘텐츠: {len(old_world)}개")
    print(f"[OK] T2 전문가 소스: {len(expert)}개")
    print(f"[OK] 일일 브리핑 목적: {len(briefing)}개")
    print(f"[OK] 영국 소스: {len(uk)}개")
    print(f"[OK] Cabernet Sauvignon 엔티티: {len(grape_items)}개")
    print(f"\n데이터베이스: {db_path}")
    print("\n다음 단계:")
    print("  - main.py에서 정기적 수집 스케줄러 구현")
    print("  - HTML Collector로 Wine21, Wine Review 활성화")
    print("  - 벡터 인덱스로 유사 콘텐츠 검색 구현")
    print("  - MCP 서버로 Claude Desktop 연동")


if __name__ == "__main__":
    main()
