# -*- coding: utf-8 -*-
"""Collector 프로토콜 및 공통 타입 정의."""

from typing import Protocol, Iterable, TypedDict
from datetime import datetime


class RawItem(TypedDict):
    id: str
    url: str
    title: str
    summary: str | None
    content: str | None
    published_at: datetime
    source_name: str
    source_type: str
    language: str | None


class Collector(Protocol):
    source_name: str
    source_type: str

    def collect(self) -> Iterable[RawItem]:
        """해당 소스에서 RawItem 시퀀스를 수집한다.

        - 네트워크/파싱 에러는 내부에서 처리하고,
          문제가 되는 아이템은 건너뛰는 방향으로 설계한다.
        """
        ...
