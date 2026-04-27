# 지리적/품종 기반 확장 설계

## 개요

WineRadar 프로젝트에 구대륙(Old World) / 신대륙(New World) 구분을 포함한 지리적 메타데이터와 포도 품종/기후대 기반 엔티티 추출 기능을 추가했습니다.

## 변경 사항

### 1. sources.yaml 확장 (20개 출처 추가)

구대륙/신대륙 균형을 고려한 공신력 있는 출처를 추가했습니다:

**구대륙 (Old World) - 7개**
- 🇫🇷 프랑스: La Revue du vin de France, IFV
- 🇮🇹 이탈리아: Gambero Rosso, Federdoc
- 🇪🇸 스페인: Vinos de España (ICEX)
- 🇩🇪 독일: Wines of Germany
- 🇵🇹 포르투갈: Wines of Portugal

**신대륙 (New World) - 7개**
- 🇺🇸 미국: Wine Institute, Wine Spectator
- 🇦🇺 호주: Wine Australia
- 🇳🇿 뉴질랜드: New Zealand Wine
- 🇨🇱 칠레: Wines of Chile
- 🇦🇷 아르헨티나: Wines of Argentina
- 🇿🇦 남아프리카공화국: Wines of South Africa (WOSA)

**새로운 필드 구조:**
```yaml
sources:
  - name: "La Revue du vin de France"
    id: "media_larvf_fr"
    type: "media"
    country: "FR"
    continent: "OLD_WORLD"
    region: "Europe/Western/France"
    tier: "premium"
    content_type: "news_review"
    language: "fr"
    weight: 3.0
```

### 2. RawItem 타입 확장

[collectors/base.py](../collectors/base.py)에 지리적/분류 메타데이터 필드 추가:

```python
class RawItem(TypedDict):
    # ... 기존 필드 ...
    country: str           # ISO 국가 코드 (KR, FR, US 등)
    continent: str         # OLD_WORLD, NEW_WORLD, ASIA 등
    region: str            # 계층적 지역 (Europe/Western/France)
    tier: str              # official, premium, community
    content_type: str      # news_review, statistics, education, market_report
```

### 3. DuckDB 스키마 확장

[graph/graph_store.py](../graph/graph_store.py)의 `urls` 테이블에 7개 컬럼 추가:

```sql
CREATE TABLE urls (
    -- ... 기존 컬럼 ...
    language TEXT,
    country TEXT,              -- ISO 국가 코드
    continent TEXT,            -- OLD_WORLD, NEW_WORLD, ASIA
    region TEXT,               -- 계층적 지역
    tier TEXT,                 -- official, premium, community
    content_type TEXT,         -- news_review, statistics, education, market_report
    -- ... 나머지 컬럼 ...
);
```

### 4. View 타입 확장

[graph/graph_queries.py](../graph/graph_queries.py)의 `get_view()` 함수에 새로운 view_type 추가:

```python
view_type: Literal[
    # 기존 엔티티 기반 뷰
    "winery", "importer", "wine", "topic", "community",
    # 지리적 관점
    "continent", "country", "region",
    # 농업/품종 관점
    "grape_variety", "climate_zone",
    # 콘텐츠 관점
    "content_type", "tier"
]
```

**사용 예시:**
```python
# 구대륙 트렌드 조회
get_view(db, "continent", focus_id="OLD_WORLD", limit=20)

# 프랑스 와인 뉴스 조회
get_view(db, "country", focus_id="FR", time_window=timedelta(days=14))

# 카베르네 소비뇽 관련 기사
get_view(db, "grape_variety", focus_id="Cabernet Sauvignon")

# 공식 기관 통계 리포트만
get_view(db, "tier", focus_id="official")
```

### 5. 엔티티 추출 모듈 설계

[analyzers/entity_extractor.py](../analyzers/entity_extractor.py) 신규 생성:

**포도 품종 사전:**
- 레드: Cabernet Sauvignon, Merlot, Pinot Noir, Syrah, Shiraz 등 14종
- 화이트: Chardonnay, Sauvignon Blanc, Riesling 등 12종

**와인 산지 사전:**
- 구대륙: Bordeaux, Burgundy, Tuscany, Rioja 등
- 신대륙: Napa Valley, Barossa Valley, Marlborough 등

**기후대 매핑:**
- Mediterranean: Bordeaux, Tuscany, Napa Valley 등
- Continental: Burgundy, Champagne, Mendoza 등
- Oceanic: Loire, Marlborough, Willamette Valley 등
- Semi-Arid: Barossa Valley, Paso Robles 등

**제공 함수:**
```python
def extract_grape_varieties(item: RawItem) -> list[Entity]
def extract_regions(item: RawItem) -> list[Entity]
def infer_climate_zone(regions: list[Entity]) -> list[Entity]
def extract_wineries(item: RawItem) -> list[Entity]
def extract_all_entities(item: RawItem) -> dict[str, list[str]]
```

## 필드 설계 철학

### Q1 답변: 관점 분석을 위한 필드 구조

| 필드 | 목적 | 활용 예시 |
|------|------|----------|
| `continent` | 대륙 수준 트렌드 비교 | "구대륙 vs 신대륙 트렌드 분석" |
| `country` | 국가별 필터링 | "프랑스 와인 뉴스만 보기" |
| `region` | 세부 산지 추적 | "보르도 vs 나파밸리 비교" |
| `tier` | 출처 신뢰도 구분 | "공식 기관 리포트만 집계" |
| `content_type` | 콘텐츠 유형별 분석 | "통계 vs 뉴스 분리" |

### Q2 답변: 뉴스·미디어 vs 통계/보고서 활용 전략

| 유형 | 활용 목적 | 스코어링 전략 |
|------|----------|--------------|
| **뉴스/미디어** (`news_review`) | 실시간 트렌드 감지, 화제성 측정 | - 시간 가중치 높음 (빠른 감소)<br>- 최신성 중시 (freshness_weight=0.4)<br>- 소셜 반응 반영 |
| **통계/보고서** (`statistics`, `market_report`) | 시장 구조 변화, 장기 추세 분석 | - 시간 가중치 낮음 (천천히 감소)<br>- 공신력 중시 (authority_weight=0.5)<br>- 심층 분석 가치 |

**적합한 뷰:**
- 뉴스: `trending_view`, `hot_winery_view`, `event_view`
- 통계: `market_analysis_view`, `industry_report_view`, `policy_update_view`

### Q3 답변: 포도 품종/기후대 중심 탐색

완전히 가능하며, 고급 사용자/전문가 분석에 강력합니다:

| 기준 | 장점 | 뷰 설계 예시 |
|------|------|-------------|
| **포도 품종** | 소비자 취향 기반 탐색 | - 피노누아 트렌드 맵<br>- 말벡 중심 생산국 비교 |
| **기후대** | 기후변화·스타일 변화 추적 | - 온대 대륙성 vs 해양성 키워드 분포<br>- 저도수 화이트 소비 증감 |
| **테루아** | 와인 전문가 타깃 | - 테루아 기반 유사 와이너리 클러스터링 |

## 데이터 흐름

```
1. Collector
   ↓ sources.yaml에서 메타데이터 로드
   ↓ RawItem에 continent, region, tier, content_type 포함

2. Analyzer
   ↓ extract_all_entities() 호출
   ↓ 포도 품종, 산지, 기후대 엔티티 추출

3. Graph Store
   ↓ urls 테이블에 지리적 메타데이터 저장
   ↓ url_entities 테이블에 엔티티 관계 저장

4. Graph Queries
   ↓ get_view(view_type="continent|grape_variety|...")
   ↓ 지리적/품종 기반 필터링

5. Reporter
   ↓ 대륙별/품종별 리포트 생성
```

## 향후 확장 가능성

1. **지리적 인덱싱**
   - `region` 필드에 지리 좌표 추가
   - 지도 기반 시각화 (Leaflet, Mapbox)

2. **품종 온톨로지**
   - 품종 계열 관계 (예: Syrah ↔ Shiraz 동의어 처리)
   - 교배 관계 (예: Cabernet Sauvignon = Cabernet Franc × Sauvignon Blanc)

3. **기후 데이터 통합**
   - 실제 기후 데이터 API 연동 (OpenWeather 등)
   - 빈티지 품질과 기후 상관관계 분석

4. **다국어 엔티티 추출**
   - 프랑스어/이탈리아어 품종명 처리
   - 한국어 와이너리명 추출 (KoNLPy)

5. **MCP 확장**
   - `get_continent_trends()` - 대륙별 트렌드 조회
   - `compare_regions()` - 산지 비교 분석
   - `find_similar_wines()` - 품종/기후대 기반 유사 와인 추천

## 관련 파일

- [config/sources.yaml](../config/sources.yaml) - 출처 정의
- [collectors/base.py](../collectors/base.py) - RawItem 타입
- [graph/graph_store.py](../graph/graph_store.py) - DuckDB 스키마
- [graph/graph_queries.py](../graph/graph_queries.py) - View 타입
- [analyzers/entity_extractor.py](../analyzers/entity_extractor.py) - 엔티티 추출
- [docs/DATA_MODEL.md](DATA_MODEL.md) - 데이터 모델 문서
