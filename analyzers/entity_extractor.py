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

    TODO:
    - title, summary, content를 결합하여 텍스트 생성
    - GRAPE_VARIETIES 사전과 매칭 (대소문자 무시)
    - 정규표현식으로 품종명 패턴 탐지
    - 신뢰도 계산 (title에서 발견: 1.0, summary: 0.8, content: 0.6)
    - Entity 리스트 반환
    """
    raise NotImplementedError


def extract_regions(item: RawItem) -> list[Entity]:
    """텍스트에서 와인 산지를 추출한다.

    Args:
        item: RawItem

    Returns:
        list[Entity]: 추출된 산지 엔티티 목록

    TODO:
    - WINE_REGIONS 사전과 매칭
    - 지역 변형 처리 (예: "Napa" → "Napa Valley")
    - 계층 구조 고려 (예: Pauillac → Bordeaux)
    """
    raise NotImplementedError


def infer_climate_zone(regions: list[Entity]) -> list[Entity]:
    """추출된 산지로부터 기후대를 추론한다.

    Args:
        regions: extract_regions()로 추출된 산지 목록

    Returns:
        list[Entity]: 추론된 기후대 엔티티 목록

    TODO:
    - regions의 각 value를 CLIMATE_ZONE_MAPPING에서 조회
    - 매칭되는 기후대를 Entity로 변환
    - 신뢰도는 region의 신뢰도 * 0.9 (추론이므로 약간 감소)
    """
    raise NotImplementedError


def extract_wineries(item: RawItem) -> list[Entity]:
    """텍스트에서 와이너리명을 추출한다.

    Args:
        item: RawItem

    Returns:
        list[Entity]: 추출된 와이너리 엔티티 목록

    TODO:
    - NER(Named Entity Recognition) 또는 사전 기반 추출
    - "Château", "Domaine", "Estate", "Winery" 등 키워드 활용
    - Phase 2에서 spaCy/KoNLPy 통합 고려
    """
    raise NotImplementedError


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

    TODO:
    - extract_grape_varieties, extract_regions, extract_wineries 호출
    - infer_climate_zone으로 기후대 추론
    - 중복 제거 및 신뢰도 기준 필터링 (threshold > 0.5)
    - dict[str, list[str]] 형태로 변환하여 반환
    """
    raise NotImplementedError
