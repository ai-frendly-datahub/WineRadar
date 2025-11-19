# -*- coding: utf-8 -*-
"""그래프 조회용 쿼리 스켈레톤."""

from typing import TypedDict, Literal, Any
from datetime import timedelta, datetime
from pathlib import Path


class ViewItem(TypedDict):
    url: str
    title: str
    summary: str | None
    published_at: datetime
    source_name: str
    source_type: str
    score: float
    entities: dict[str, list[str]]


def get_view(
    db_path: Path,
    view_type: Literal[
        # 기존 엔티티 기반 뷰
        "winery", "importer", "wine", "topic", "community",
        # 지리적 관점
        "continent", "country", "region",
        # 농업/품종 관점
        "grape_variety", "climate_zone",
        # 콘텐츠 관점
        "content_type", "tier"
    ],
    focus_id: str | None = None,
    time_window: timedelta = timedelta(days=7),
    limit: int = 50,
    source_filter: list[str] | None = None,
) -> list[ViewItem]:
    """그래프에서 특정 관점(view)으로 URL 목록을 조회한다.

    Args:
        db_path: DuckDB 데이터베이스 파일 경로
        view_type: 뷰 타입
            - 엔티티 기반: winery, importer, wine, topic, community
            - 지리적: continent (OLD_WORLD/NEW_WORLD), country (FR/US/AU 등), region (Bordeaux, Napa 등)
            - 농업/품종: grape_variety (Cabernet Sauvignon 등), climate_zone (Mediterranean 등)
            - 콘텐츠: content_type (news_review/statistics 등), tier (official/premium/community)
        focus_id: 중심 엔티티 ID (None이면 전체 TOP)
            - continent view: "OLD_WORLD" or "NEW_WORLD"
            - country view: "FR", "US", "AU" 등 ISO 국가 코드
            - grape_variety view: "Cabernet Sauvignon", "Pinot Noir" 등
            - climate_zone view: "Mediterranean", "Continental" 등
        time_window: 시간 범위 (기본 7일)
        limit: 최대 개수
        source_filter: 소스 필터 (예: ["Wine21", "Decanter"])

    Returns:
        list[ViewItem]: ViewItem 목록 (score 내림차순 정렬)

    Examples:
        # 구대륙 트렌드 조회
        get_view(db, "continent", focus_id="OLD_WORLD", limit=20)

        # 프랑스 와인 뉴스 조회
        get_view(db, "country", focus_id="FR", time_window=timedelta(days=14))

        # 카베르네 소비뇽 관련 기사
        get_view(db, "grape_variety", focus_id="Cabernet Sauvignon")

        # 공식 기관 통계 리포트만
        get_view(db, "tier", focus_id="official")

    TODO:
    - graph_store 에서 최근 time_window 범위 내 URL 노드 로드
    - view_type / focus_id 에 따라 관련 URL 필터링
    - 지리적 뷰는 urls 테이블의 continent/country/region 컬럼 사용
    - 품종/기후대 뷰는 url_entities 테이블의 entity_type 사용
    - scoring 모듈을 사용해서 score 계산 후 정렬
    - ViewItem 리스트 반환
    """
    raise NotImplementedError
