# -*- coding: utf-8 -*-
"""엔티티 추출 모듈.

와인 관련 텍스트에서 다양한 엔티티를 추출한다:
- winery: 와이너리명 (예: Château Margaux, Penfolds)
- importer: 수입사명 (예: 와인앤모어, 신세계L&B)
- wine: 특정 와인명 (예: Opus One, Grange)
- grape_variety: 포도 품종 (예: Cabernet Sauvignon, Pinot Noir)
- region: 와인 생산지 (예: Bordeaux, Napa Valley, Barossa)
- climate_zone: 기후대 (예: Mediterranean, Continental, Oceanic)
- topic: 키워드/토픽 (예: 빈티지, 수상, 페어링)
"""

from importlib import import_module
from typing import Optional, Protocol, TypedDict, cast
import re
from collectors.base import RawItem


class Entity(TypedDict):
    """추출된 엔티티."""

    type: str  # winery, grape_variety, climate_zone 등
    value: str  # 엔티티 값 (예: "Cabernet Sauvignon")
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    source: str  # title, summary, content 중 어디서 추출되었는지


# Import expanded entity dictionaries
from analyzers.wine_entities_data import (
    GRAPE_VARIETIES_EXPANDED,
    WINE_REGIONS_EXPANDED,
    CLIMATE_ZONE_MAPPING_EXPANDED,
    KNOWN_WINERIES_EXPANDED,
)
from analyzers.entity_normalizer import (
    normalize_unicode,
    normalize_entity,
    calculate_entity_confidence,
    deduplicate_entities,
)

# Use expanded dictionaries
GRAPE_VARIETIES = GRAPE_VARIETIES_EXPANDED
WINE_REGIONS = WINE_REGIONS_EXPANDED
CLIMATE_ZONE_MAPPING = CLIMATE_ZONE_MAPPING_EXPANDED
KNOWN_WINERIES = KNOWN_WINERIES_EXPANDED

_keyword_pattern_cache: dict[str, Optional[re.Pattern[str]]] = {}


class _KoreanAnalyzerLike(Protocol):
    _kiwi: Optional[object]

    def match_keyword(self, text: str, keyword: str) -> bool: ...


def _load_korean_analyzer_constructor() -> Optional[type[_KoreanAnalyzerLike]]:
    try:
        korean_analyzer_module = import_module("radar_core.common.korean_analyzer")
    except ModuleNotFoundError:
        return None

    korean_analyzer_constructor = getattr(korean_analyzer_module, "KoreanAnalyzer", None)
    if korean_analyzer_constructor is None:
        return None

    return cast(type[_KoreanAnalyzerLike], korean_analyzer_constructor)


_KOREAN_ANALYZER_CONSTRUCTOR = _load_korean_analyzer_constructor()
_korean_analyzer: Optional[_KoreanAnalyzerLike] = None
_korean_analyzer_initialized = False


def _is_ascii_only(keyword: str) -> bool:
    return all(ord(char) < 128 for char in keyword)


def _get_keyword_pattern(keyword: str) -> Optional[re.Pattern[str]]:
    if keyword in _keyword_pattern_cache:
        return _keyword_pattern_cache[keyword]

    pattern = (
        re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
        if _is_ascii_only(keyword)
        else None
    )
    _keyword_pattern_cache[keyword] = pattern
    return pattern


def _get_korean_analyzer() -> Optional[_KoreanAnalyzerLike]:
    global _korean_analyzer
    global _korean_analyzer_initialized

    if _korean_analyzer_initialized:
        return _korean_analyzer

    _korean_analyzer_initialized = True
    if _KOREAN_ANALYZER_CONSTRUCTOR is not None:
        _korean_analyzer = _KOREAN_ANALYZER_CONSTRUCTOR()

    return _korean_analyzer


def _keyword_in_text(keyword: str, text: str, text_lower: str) -> bool:
    normalized = keyword.lower()
    if not normalized:
        return False

    pattern = _get_keyword_pattern(normalized)
    if pattern is not None and pattern.search(text):
        return True

    korean_analyzer = _get_korean_analyzer()
    if korean_analyzer is not None and getattr(korean_analyzer, "_kiwi", None) is not None:
        return korean_analyzer.match_keyword(text, keyword)

    if normalized in text_lower:
        return True

    normalized_ascii = normalize_unicode(normalized)
    text_ascii = normalize_unicode(text_lower)
    return normalized_ascii in text_ascii


# spaCy 모델(옵션)
try:  # pragma: no cover - 모델이 없으면 규칙만 사용
    spacy_module = import_module("spacy")
    _nlp = spacy_module.load("en_core_web_sm")
except Exception:  # pragma: no cover
    _nlp = None


def extract_grape_varieties(item: RawItem) -> list[Entity]:
    """텍스트에서 포도 품종을 추출한다.

    Args:
        item: RawItem (title, summary, content 포함)

    Returns:
        list[Entity]: 추출된 포도 품종 엔티티 목록
    """
    entities: list[Entity] = []

    # title, summary, content에서 각각 추출 (신뢰도 다르게)
    sources = [
        ("title", item.get("title", ""), 1.0),
        ("summary", item.get("summary", ""), 0.8),
        ("content", item.get("content", ""), 0.6),
    ]

    found_varieties: dict[str, tuple[str, float]] = {}  # variety -> (source, confidence)

    for source_name, text, confidence in sources:
        if not text:
            continue

        text_lower = text.lower()

        for variety in GRAPE_VARIETIES:
            if _keyword_in_text(variety, text, text_lower):
                # 이미 발견된 품종이면 더 높은 신뢰도로 업데이트
                if variety not in found_varieties or confidence > found_varieties[variety][1]:
                    found_varieties[variety] = (source_name, confidence)

    # Entity 리스트로 변환
    for variety, (source, confidence) in found_varieties.items():
        entities.append(
            {
                "type": "grape_variety",
                "value": variety,
                "confidence": confidence,
                "source": source,
            }
        )

    return entities


def extract_regions(item: RawItem) -> list[Entity]:
    """텍스트에서 와인 산지를 추출한다.

    Args:
        item: RawItem

    Returns:
        list[Entity]: 추출된 산지 엔티티 목록
    """
    entities: list[Entity] = []

    sources = [
        ("title", item.get("title", ""), 1.0),
        ("summary", item.get("summary", ""), 0.8),
        ("content", item.get("content", ""), 0.6),
    ]

    found_regions: dict[str, tuple[str, float]] = {}

    for source_name, text, confidence in sources:
        if not text:
            continue

        text_lower = text.lower()

        for region in WINE_REGIONS:
            if _keyword_in_text(region, text, text_lower):
                if region not in found_regions or confidence > found_regions[region][1]:
                    found_regions[region] = (source_name, confidence)

    for region, (source, confidence) in found_regions.items():
        entities.append(
            {
                "type": "region",
                "value": region,
                "confidence": confidence,
                "source": source,
            }
        )

    region_values = [entity["value"].lower() for entity in entities]
    filtered_entities: list[Entity] = []
    for entity in entities:
        value_lower = entity["value"].lower()
        has_longer_region = any(
            other != value_lower and value_lower in other for other in region_values
        )
        if not has_longer_region:
            filtered_entities.append(entity)

    return filtered_entities


def infer_climate_zone(regions: list[Entity]) -> list[Entity]:
    """추출된 산지로부터 기후대를 추론한다.

    Args:
        regions: extract_regions()로 추출된 산지 목록

    Returns:
        list[Entity]: 추론된 기후대 엔티티 목록
    """
    climate_zones: dict[str, tuple[str, float]] = {}  # zone -> (source, confidence)

    for region_entity in regions:
        region_value = region_entity["value"]
        region_confidence = region_entity["confidence"]
        region_source = region_entity["source"]

        # CLIMATE_ZONE_MAPPING에서 해당 region을 찾기
        for climate_zone, zone_regions in CLIMATE_ZONE_MAPPING.items():
            if region_value in zone_regions:
                inferred_confidence = region_confidence * 0.9  # 추론이므로 90%로 감소

                # 더 높은 신뢰도로 업데이트
                if (
                    climate_zone not in climate_zones
                    or inferred_confidence > climate_zones[climate_zone][1]
                ):
                    climate_zones[climate_zone] = (region_source, inferred_confidence)

    # Entity 리스트로 변환
    entities: list[Entity] = []
    for zone, (source, confidence) in climate_zones.items():
        entities.append(
            {
                "type": "climate_zone",
                "value": zone,
                "confidence": confidence,
                "source": source,
            }
        )

    return entities


def extract_wineries(item: RawItem) -> list[Entity]:
    """텍스트에서 와이너리명을 추출한다.

    Args:
        item: RawItem

    Returns:
        list[Entity]: 추출된 와이너리 엔티티 목록
    """
    entities: list[Entity] = []

    sources = [
        ("title", item.get("title", ""), 1.0),
        ("summary", item.get("summary", ""), 0.8),
        ("content", item.get("content", ""), 0.6),
    ]

    found_wineries: dict[str, tuple[str, float]] = {}

    for source_name, text, confidence in sources:
        if not text:
            continue

        # 알려진 와이너리 매칭 (대소문자 무시)
        text_lower = text.lower()
        for winery in KNOWN_WINERIES:
            if _keyword_in_text(winery, text, text_lower):
                if winery not in found_wineries or confidence > found_wineries[winery][1]:
                    found_wineries[winery] = (source_name, confidence)

        for matched in re.finditer(
            r"\bch[âa]teau\s+[A-Za-zÀ-ÖØ-öø-ÿ'\-]+",
            text,
            flags=re.IGNORECASE,
        ):
            winery_name = matched.group(0)
            if winery_name not in found_wineries or confidence > found_wineries[winery_name][1]:
                found_wineries[winery_name] = (source_name, confidence)

    for winery, (source, confidence) in found_wineries.items():
        entities.append(
            {
                "type": "winery",
                "value": winery,
                "confidence": confidence,
                "source": source,
            }
        )

    return entities


def extract_all_entities(item: RawItem) -> dict[str, list[str]]:
    """RawItem에서 모든 타입의 엔티티를 추출한다.

    Args:
        item: RawItem

    Returns:
        dict[str, list[str]]: 엔티티 타입별 값 목록
            예: {
                "grape_variety": ["Cabernet Sauvignon", "Merlot"],
                "region": ["Bordeaux"],
                "climate_zone": ["Mediterranean"],
                "winery": ["Château Margaux"]
            }
    """
    # 각 타입별 엔티티 추출
    grape_entities = extract_grape_varieties(item)
    region_entities = extract_regions(item)
    winery_entities = extract_wineries(item)
    climate_entities = infer_climate_zone(region_entities)

    if _nlp:
        doc = _nlp(
            " ".join(
                filter(None, [item.get("title"), item.get("summary"), item.get("content", "")])
            )
        )
        for ent in doc.ents:
            if ent.label_ in {"ORG", "PERSON"}:
                winery_entities.append(
                    {"type": "winery", "value": ent.text, "confidence": 0.55, "source": "spacy"}
                )
            if ent.label_ == "LOC":
                region_entities.append(
                    {"type": "region", "value": ent.text, "confidence": 0.55, "source": "spacy"}
                )

    # 모든 엔티티 통합
    all_entities = grape_entities + region_entities + winery_entities + climate_entities

    # 정규화 및 중복 제거 (동일 엔티티의 다양한 표기 통합)
    deduplicated = deduplicate_entities([dict(entity) for entity in all_entities])

    # 신뢰도 필터링 (threshold > 0.5)
    filtered_entities = [e for e in deduplicated if e["confidence"] > 0.5]

    # dict[str, list[str]] 형태로 변환
    result: dict[str, list[str]] = {}

    for entity in filtered_entities:
        entity_type = entity["type"]
        entity_value = entity["value"]

        if entity_type not in result:
            result[entity_type] = []

        # 중복 제거 (이미 deduplicate_entities에서 처리했지만 추가 보호)
        if entity_value not in result[entity_type]:
            result[entity_type].append(entity_value)

    # 각 타입별로 정렬
    for entity_type in result:
        result[entity_type] = sorted(result[entity_type])

    return result
