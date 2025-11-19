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

from typing import TypedDict
from collectors.base import RawItem


class Entity(TypedDict):
    """추출된 엔티티."""
    type: str  # winery, grape_variety, climate_zone 등
    value: str  # 엔티티 값 (예: "Cabernet Sauvignon")
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    source: str  # title, summary, content 중 어디서 추출되었는지


# spaCy 모델(옵션)
try:  # pragma: no cover - 모델이 없으면 규칙만 사용
    import spacy

    _NLP = spacy.load("en_core_web_sm")
except Exception:  # pragma: no cover
    _NLP = None


# 주요 포도 품종 사전 (확장 가능)
GRAPE_VARIETIES = {
    # 레드 품종
    "Cabernet Sauvignon", "Merlot", "Pinot Noir", "Syrah", "Shiraz",
    "Grenache", "Tempranillo", "Sangiovese", "Nebbiolo", "Malbec",
    "Zinfandel", "Carmenere", "Petit Verdot", "Mourvèdre",
    # 화이트 품종
    "Chardonnay", "Sauvignon Blanc", "Riesling", "Pinot Grigio", "Pinot Gris",
    "Gewürztraminer", "Viognier", "Chenin Blanc", "Sémillon", "Albariño",
    "Moscato", "Grüner Veltliner",
}

# 주요 와인 산지 (확장 가능)
WINE_REGIONS = {
    # 구대륙
    "Bordeaux", "Burgundy", "Champagne", "Rhône", "Loire", "Alsace",
    "Tuscany", "Piedmont", "Veneto", "Rioja", "Ribera del Duero", "Priorat",
    "Douro", "Mosel", "Rheingau", "Pfalz",
    # 신대륙
    "Napa Valley", "Sonoma", "Paso Robles", "Willamette Valley",
    "Barossa Valley", "Margaret River", "Marlborough", "Central Otago",
    "Mendoza", "Maipo Valley", "Colchagua Valley", "Stellenbosch",
}

# 기후대 매핑 (region → climate_zone)
CLIMATE_ZONE_MAPPING = {
    # 지중해성 기후
    "Mediterranean": [
        "Bordeaux", "Tuscany", "Rioja", "Douro", "Napa Valley", "Margaret River"
    ],
    # 대륙성 기후
    "Continental": [
        "Burgundy", "Champagne", "Piedmont", "Mosel", "Rheingau", "Mendoza"
    ],
    # 해양성 기후
    "Oceanic": [
        "Loire", "Marlborough", "Willamette Valley", "Sonoma"
    ],
    # 준건조 기후
    "Semi-Arid": [
        "Ribera del Duero", "Priorat", "Barossa Valley", "Paso Robles"
    ],
}


def extract_grape_varieties(item: RawItem) -> list[Entity]:
    """텍스트에서 포도 품종을 추출한다.

    Args:
        item: RawItem (title, summary, content 포함)

    Returns:
        list[Entity]: 추출된 포도 품종 엔티티 목록
    """
    import re

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
            pattern = r'\b' + re.escape(variety.lower()) + r'\b'
            if re.search(pattern, text_lower):
                # 이미 발견된 품종이면 더 높은 신뢰도로 업데이트
                if variety not in found_varieties or confidence > found_varieties[variety][1]:
                    found_varieties[variety] = (source_name, confidence)

    # Entity 리스트로 변환
    for variety, (source, confidence) in found_varieties.items():
        entities.append({
            "type": "grape_variety",
            "value": variety,
            "confidence": confidence,
            "source": source,
        })

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
            pattern = r'\b' + re.escape(region.lower()) + r'\b'
            if re.search(pattern, text_lower):
                if region not in found_regions or confidence > found_regions[region][1]:
                    found_regions[region] = (source_name, confidence)

    for region, (source, confidence) in found_regions.items():
        entities.append({
            "type": "region",
            "value": region,
            "confidence": confidence,
            "source": source,
        })

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
                if climate_zone not in climate_zones or inferred_confidence > climate_zones[climate_zone][1]:
                    climate_zones[climate_zone] = (region_source, inferred_confidence)

    # Entity 리스트로 변환
    entities: list[Entity] = []
    for zone, (source, confidence) in climate_zones.items():
        entities.append({
            "type": "climate_zone",
            "value": zone,
            "confidence": confidence,
            "source": source,
        })

    return entities


def extract_wineries(item: RawItem) -> list[Entity]:
    """텍스트에서 와이너리명을 추출한다.

    Args:
        item: RawItem

    Returns:
        list[Entity]: 추출된 와이너리 엔티티 목록
    """
    import re

    # 유명 와이너리 사전 (확장 가능)
    KNOWN_WINERIES = {
        # 프랑스 보르도
        "Château Lafite", "Château Margaux", "Château Latour",
        "Château Mouton Rothschild", "Château Haut-Brion", "Pétrus",
        "Château d'Yquem", "Château Lynch-Bages", "Château Palmer",

        # 프랑스 부르고뉴
        "Domaine de la Romanée-Conti", "Domaine Leflaive", "Domaine Leroy",

        # 이탈리아
        "Antinori", "Gaja", "Sassicaia", "Ornellaia", "Masseto",

        # 미국
        "Opus One", "Screaming Eagle", "Harlan Estate", "Ridge Vineyards",

        # 호주
        "Penfolds", "Henschke",

        # 스페인
        "Vega Sicilia", "Pingus",
    }

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
            pattern = r'\b' + re.escape(winery.lower()) + r'\b'
            if re.search(pattern, text_lower):
                if winery not in found_wineries or confidence > found_wineries[winery][1]:
                    found_wineries[winery] = (source_name, confidence)

    for winery, (source, confidence) in found_wineries.items():
        entities.append({
            "type": "winery",
            "value": winery,
            "confidence": confidence,
            "source": source,
        })

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

    if _NLP:
        doc = _NLP(" ".join(filter(None, [item.get("title"), item.get("summary"), item.get("content", "")])))
        for ent in doc.ents:
            if ent.label_ in {"ORG", "PERSON"}:
                winery_entities.append({"type": "winery", "value": ent.text, "confidence": 0.55, "source": "spacy"})
            if ent.label_ == "LOC":
                region_entities.append({"type": "region", "value": ent.text, "confidence": 0.55, "source": "spacy"})

    # 모든 엔티티 통합
    all_entities = grape_entities + region_entities + winery_entities + climate_entities

    # 신뢰도 필터링 (threshold > 0.5)
    filtered_entities = [e for e in all_entities if e["confidence"] > 0.5]

    # dict[str, list[str]] 형태로 변환
    result: dict[str, list[str]] = {}

    for entity in filtered_entities:
        entity_type = entity["type"]
        entity_value = entity["value"]

        if entity_type not in result:
            result[entity_type] = []

        # 중복 제거
        if entity_value not in result[entity_type]:
            result[entity_type].append(entity_value)

    # 각 타입별로 정렬
    for entity_type in result:
        result[entity_type] = sorted(result[entity_type])

    return result
