# -*- coding: utf-8 -*-
"""그래프 조회용 쿼리 스켈레톤."""

from typing import TypedDict, Literal, Any
from datetime import timedelta, datetime


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
    view_type: Literal["winery", "importer", "wine", "topic", "community"],
    focus_id: str | None,
    time_window: timedelta,
    limit: int = 50,
    source_filter: list[str] | None = None,
) -> list[ViewItem]:
    """그래프에서 특정 관점(view)으로 URL 목록을 조회한다.

    TODO:
    - graph_store 에서 최근 time_window 범위 내 URL 노드 로드
    - view_type / focus_id 에 따라 관련 URL 필터링
    - scoring 모듈을 사용해서 score 계산 후 정렬
    - ViewItem 리스트 반환
    """
    raise NotImplementedError
