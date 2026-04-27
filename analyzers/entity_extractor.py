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

import html
import re
from typing import TypedDict

from collectors.base import RawItem


class Entity(TypedDict):
    """추출된 엔티티."""

    type: str  # winery, grape_variety, climate_zone 등
    value: str  # 엔티티 값 (예: "Cabernet Sauvignon")
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    source: str  # title, summary, content 중 어디서 추출되었는지


# Import expanded entity dictionaries
from analyzers.entity_normalizer import (  # noqa: E402
    deduplicate_entities,
)
from analyzers.wine_entities_data import (  # noqa: E402
    CLIMATE_ZONE_MAPPING_EXPANDED,
    GRAPE_VARIETIES_EXPANDED,
    KNOWN_WINERIES_EXPANDED,
    TOPIC_KEYWORDS_EXPANDED,
    WINE_REGIONS_EXPANDED,
)


# Use expanded dictionaries
GRAPE_VARIETIES = GRAPE_VARIETIES_EXPANDED
WINE_REGIONS = WINE_REGIONS_EXPANDED
CLIMATE_ZONE_MAPPING = CLIMATE_ZONE_MAPPING_EXPANDED
KNOWN_WINERIES = KNOWN_WINERIES_EXPANDED | {"Château Lafite"}
TOPIC_KEYWORDS = TOPIC_KEYWORDS_EXPANDED

# spaCy 모델(옵션)
try:  # pragma: no cover - 모델이 없으면 규칙만 사용
    import spacy

    _NLP = spacy.load("en_core_web_sm")
except Exception:  # pragma: no cover
    _NLP = None


def _matches_keyword(text_lower: str, keyword: str) -> bool:
    keyword_lower = keyword.lower().strip()
    if not keyword_lower:
        return False
    if keyword_lower.isascii():
        pattern = rf"(?<![0-9a-z]){re.escape(keyword_lower)}(?![0-9a-z])"
        return re.search(pattern, text_lower) is not None
    return keyword_lower in text_lower


def _topic_text(text: object) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"<[^>]+>", " ", html.unescape(text))


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
            # 단어 경계를 고려한 매칭
            pattern = r"\b" + re.escape(variety.lower()) + r"\b"
            if re.search(pattern, text_lower):
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


def extract_topics(item: RawItem) -> list[Entity]:
    """텍스트에서 와인 시장/행사/정책/교육 토픽을 추출한다."""
    entities: list[Entity] = []
    sources = [
        ("title", item.get("title", ""), 1.0),
        ("summary", item.get("summary", ""), 0.8),
        ("content", item.get("content", ""), 0.6),
    ]
    found_topics: dict[str, tuple[str, float]] = {}

    for source_name, text, confidence in sources:
        normalized_text = _topic_text(text)
        if not normalized_text:
            continue
        text_lower = normalized_text.lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(_matches_keyword(text_lower, keyword) for keyword in keywords):
                if topic not in found_topics or confidence > found_topics[topic][1]:
                    found_topics[topic] = (source_name, confidence)

    for topic, (source, confidence) in found_topics.items():
        entities.append(
            {
                "type": "topic",
                "value": topic,
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
    import re

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
            if _matches_keyword(text_lower, region):
                if region not in found_regions or confidence > found_regions[region][1]:
                    found_regions[region] = (source_name, confidence)

    region_names = list(found_regions)
    subsumed_regions = {
        region
        for region in region_names
        for other in region_names
        if region != other and region.lower() in other.lower() and len(region) < len(other)
    }

    for region, (source, confidence) in found_regions.items():
        if region in subsumed_regions:
            continue
        entities.append(
            {
                "type": "region",
                "value": region,
                "confidence": confidence,
                "source": source,
            }
        )

    return entities


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
    import re

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
            pattern = r"\b" + re.escape(winery.lower()) + r"\b"
            if re.search(pattern, text_lower):
                if winery not in found_wineries or confidence > found_wineries[winery][1]:
                    found_wineries[winery] = (source_name, confidence)

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


def _validate_extraction_input(item: RawItem) -> list[str]:
    """Validate RawItem has sufficient text for entity extraction.

    Returns:
        List of warning messages (empty if valid).
    """
    warnings: list[str] = []

    title = item.get("title", "")
    summary = item.get("summary")
    content = item.get("content", "")

    if not title and not summary and not content:
        warnings.append("No text fields available for entity extraction")
        return warnings

    if title and len(title.strip()) < 3:
        warnings.append(f"Title too short for reliable extraction: '{title}'")

    return warnings


def _validate_entity(entity: Entity) -> bool:
    """Validate a single extracted entity for common issues.

    Returns:
        True if entity is valid, False otherwise.
    """
    from analyzers.entity_normalizer import validate_entity_value

    value = entity.get("value", "")
    entity_type = entity.get("type", "")

    if not value or not entity_type:
        return False

    if not isinstance(value, str) or len(value.strip()) < 2:
        return False

    validation_warnings = validate_entity_value(entity_type, value)
    return len(validation_warnings) == 0


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
    import logging

    _log = logging.getLogger(__name__)

    input_warnings = _validate_extraction_input(item)
    if input_warnings:
        for warning in input_warnings:
            _log.warning("Entity extraction input validation: %s", warning)
        if any("No text fields" in w for w in input_warnings):
            return {}

    try:
        grape_entities = extract_grape_varieties(item)
    except Exception as exc:
        _log.warning("Grape variety extraction failed: %s", exc)
        grape_entities = []

    try:
        region_entities = extract_regions(item)
    except Exception as exc:
        _log.warning("Region extraction failed: %s", exc)
        region_entities = []

    try:
        winery_entities = extract_wineries(item)
    except Exception as exc:
        _log.warning("Winery extraction failed: %s", exc)
        winery_entities = []

    try:
        topic_entities = extract_topics(item)
    except Exception as exc:
        _log.warning("Topic extraction failed: %s", exc)
        topic_entities = []

    try:
        climate_entities = infer_climate_zone(region_entities)
    except Exception as exc:
        _log.warning("Climate zone inference failed: %s", exc)
        climate_entities = []

    if _NLP:
        try:
            doc = _NLP(
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
        except Exception as exc:
            _log.warning("spaCy NER extraction failed: %s", exc)

    all_entities = (
        grape_entities + region_entities + winery_entities + topic_entities + climate_entities
    )

    pre_validation_count = len(all_entities)
    all_entities = [e for e in all_entities if _validate_entity(e)]
    if len(all_entities) < pre_validation_count:
        _log.info(
            "Filtered %d invalid entities out of %d",
            pre_validation_count - len(all_entities),
            pre_validation_count,
        )

    deduplicated = deduplicate_entities(all_entities)

    filtered_entities = [e for e in deduplicated if e["confidence"] > 0.5]

    result: dict[str, list[str]] = {}

    for entity in filtered_entities:
        entity_type = entity["type"]
        entity_value = entity["value"]

        if entity_type not in result:
            result[entity_type] = []

        if entity_value not in result[entity_type]:
            result[entity_type].append(entity_value)

    for entity_type in result:
        result[entity_type] = sorted(result[entity_type])

    return result
