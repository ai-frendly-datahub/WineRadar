# -*- coding: utf-8 -*-
"""그래프 스토어 스켈레톤.

- 노드/엣지 저장 방식은 SQLite, 파일 기반 등 자유롭게 선택 가능
- Codex/Claude Code로 실제 구현을 점진적으로 채워 넣는 것을 전제로 함
"""

from typing import TypedDict, Any
from datetime import datetime


class Node(TypedDict):
    id: str
    type: str
    name: str
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class Edge(TypedDict):
    source_id: str
    target_id: str
    type: str
    weight: float
    first_seen_at: datetime
    last_seen_at: datetime


def upsert_url_and_entities(item, entities, now: datetime) -> None:
    """URL 및 관련 엔티티 노드/엣지를 upsert.

    TODO:
    - 간단한 저장 백엔드(SQLite, JSON 등) 선택
    - Node/Edge 삽입/갱신 로직 구현
    """
    raise NotImplementedError


def prune_expired_urls(now: datetime, ttl_days: int = 30) -> None:
    """ttl_days 이전의 URL 노드 및 관련 엣지를 삭제.

    TODO:
    - 저장 방식에 맞는 TTL/Pruning 로직 구현
    """
    raise NotImplementedError
