"""View 쿼리 사용자 뷰 중심 메타데이터 타입 검증 테스트."""

from __future__ import annotations

from typing import Optional, get_type_hints

import pytest

from graph.graph_queries import ViewItem


pytestmark = pytest.mark.unit


def test_view_item_has_required_fields() -> None:
    """ViewItem TypedDict가 모든 필수 필드를 정의하고 있는지 검증."""
    type_hints = get_type_hints(ViewItem)

    required_fields = {
        # 콘텐츠 필드
        "url",
        "title",
        "summary",
        "published_at",
        "source_name",
        "source_type",
        "content_type",
        # 사용자 뷰 중심 메타데이터
        "country",
        "continent",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
        # 스코어 및 엔티티
        "score",
        "entities",
    }

    actual_fields = set(type_hints.keys())
    assert required_fields == actual_fields, (
        f"ViewItem 필드 불일치. "
        f"누락: {required_fields - actual_fields}, "
        f"초과: {actual_fields - required_fields}"
    )


def test_view_item_metadata_types() -> None:
    """ViewItem 메타데이터 필드의 타입이 올바른지 검증."""
    from datetime import datetime

    type_hints = get_type_hints(ViewItem)

    # 문자열 필드
    assert type_hints["url"] == str
    assert type_hints["title"] == str
    assert type_hints["source_name"] == str
    assert type_hints["source_type"] == str
    assert type_hints["content_type"] == str
    assert type_hints["country"] == str
    assert type_hints["continent"] == str
    assert type_hints["region"] == str
    assert type_hints["producer_role"] == str
    assert type_hints["trust_tier"] == str
    assert type_hints["collection_tier"] == str

    # Optional 문자열 필드
    assert type_hints["summary"] == Optional[str]

    # datetime 필드
    assert type_hints["published_at"] == datetime

    # 배열 필드
    assert type_hints["info_purpose"] == list[str]

    # float 필드
    assert type_hints["score"] == float

    # dict 필드
    assert type_hints["entities"] == dict[str, list[str]]


def test_view_item_matches_raw_item_metadata() -> None:
    """ViewItem 메타데이터가 RawItem과 일치하는지 검증."""
    from collectors.base import RawItem

    view_hints = get_type_hints(ViewItem)
    raw_hints = get_type_hints(RawItem)

    # 공통 메타데이터 필드
    common_metadata = {
        "country",
        "continent",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
    }

    for field in common_metadata:
        assert field in view_hints, f"ViewItem에 {field} 필드 누락"
        assert field in raw_hints, f"RawItem에 {field} 필드 누락"


def test_view_item_info_purpose_is_list() -> None:
    """ViewItem의 info_purpose가 list[str] 타입인지 검증."""
    import typing

    type_hints = get_type_hints(ViewItem)

    assert typing.get_origin(type_hints["info_purpose"]) == list
    list_args = typing.get_args(type_hints["info_purpose"])
    assert len(list_args) == 1
    assert list_args[0] == str


def test_view_item_score_is_float() -> None:
    """ViewItem의 score가 float 타입인지 검증."""
    type_hints = get_type_hints(ViewItem)

    assert type_hints["score"] == float


def test_view_item_entities_structure() -> None:
    """ViewItem의 entities가 올바른 구조인지 검증."""
    import typing

    type_hints = get_type_hints(ViewItem)

    # dict[str, list[str]] 타입 확인
    assert typing.get_origin(type_hints["entities"]) == dict

    dict_args = typing.get_args(type_hints["entities"])
    assert len(dict_args) == 2
    assert dict_args[0] == str  # 키 타입

    # 값 타입: list[str]
    value_type = dict_args[1]
    assert typing.get_origin(value_type) == list
    assert typing.get_args(value_type)[0] == str


def test_get_view_supports_user_view_metadata() -> None:
    """get_view 함수가 사용자 뷰 중심 메타데이터 view_type을 지원하는지 검증."""
    import typing

    from graph.graph_queries import get_view

    # get_view 함수 시그니처 가져오기
    sig = typing.get_type_hints(get_view)

    # view_type Literal 값 추출
    view_type_hint = sig["view_type"]
    view_types = typing.get_args(view_type_hint)

    # 사용자 뷰 중심 메타데이터 view_type 확인
    required_view_types = {
        "continent",
        "country",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
        "content_type",
    }

    for vt in required_view_types:
        assert vt in view_types, f"get_view가 '{vt}' view_type을 지원하지 않음"


def test_get_view_return_type() -> None:
    """get_view 함수의 반환 타입이 list[ViewItem]인지 검증."""
    import typing

    from graph.graph_queries import get_view

    sig = typing.get_type_hints(get_view)
    return_type = sig["return"]

    assert typing.get_origin(return_type) == list
    list_args = typing.get_args(return_type)
    assert len(list_args) == 1
    assert list_args[0] == ViewItem


def test_get_view_parameters() -> None:
    """get_view 함수가 필수 파라미터를 가지는지 검증."""
    import inspect

    from graph.graph_queries import get_view

    sig = inspect.signature(get_view)
    params = sig.parameters

    # 필수 파라미터 확인
    assert "db_path" in params
    assert "view_type" in params

    # Optional 파라미터 확인
    assert "focus_id" in params
    assert "time_window" in params
    assert "limit" in params
    assert "source_filter" in params

    # 기본값 확인
    assert params["focus_id"].default is None
    assert params["limit"].default == 50
    assert params["source_filter"].default is None


def test_view_item_has_all_db_schema_metadata() -> None:
    """ViewItem이 DuckDB urls 테이블의 모든 메타데이터 컬럼을 포함하는지 검증."""
    type_hints = get_type_hints(ViewItem)

    # DuckDB urls 테이블의 사용자 뷰 메타데이터 컬럼
    db_metadata_columns = {
        "country",
        "continent",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
    }

    for column in db_metadata_columns:
        assert column in type_hints, f"ViewItem에 '{column}' 필드 누락"


def test_view_item_content_fields() -> None:
    """ViewItem이 콘텐츠 필드를 올바르게 정의하는지 검증."""
    type_hints = get_type_hints(ViewItem)

    content_fields = {
        "url",
        "title",
        "summary",
        "published_at",
        "source_name",
        "source_type",
        "content_type",
    }

    for field in content_fields:
        assert field in type_hints, f"ViewItem에 '{field}' 필드 누락"


def test_view_item_optional_fields() -> None:
    """ViewItem의 Optional 필드가 올바르게 정의되었는지 검증."""
    type_hints = get_type_hints(ViewItem)

    # summary만 Optional
    assert type_hints["summary"] == Optional[str]


def test_view_type_literal_values() -> None:
    """get_view의 view_type Literal이 올바른 값들을 가지는지 검증."""
    import typing

    from graph.graph_queries import get_view

    sig = typing.get_type_hints(get_view)
    view_type_hint = sig["view_type"]
    view_types = typing.get_args(view_type_hint)

    # 모든 예상 view_type 확인
    expected_view_types = {
        # 엔티티 기반
        "winery",
        "importer",
        "wine",
        "topic",
        "community",
        # 지리적
        "continent",
        "country",
        "region",
        # 사용자 뷰 메타데이터
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
        # 농업/품종
        "grape_variety",
        "climate_zone",
        # 콘텐츠
        "content_type",
    }

    assert set(view_types) == expected_view_types, (
        f"view_type 불일치. "
        f"누락: {expected_view_types - set(view_types)}, "
        f"초과: {set(view_types) - expected_view_types}"
    )
