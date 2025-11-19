# 소비자 와인 플랫폼 분석 (Consumer Wine Platforms Analysis)

## 개요

ChatGPT 대화에서 확인된 주요 소비자 와인 플랫폼 5개를 분석하여 WineRadar 데이터 소스로의 통합 가능성을 평가합니다.

## 확인된 플랫폼 (5개)

### 1. Delectable Wine
**설명**: 와인 병 사진 촬영으로 스캔 및 평점 기능 제공

**주요 기능:**
- 이미지 인식 (Wine bottle scanning)
- 사용자 평점 및 리뷰
- 소믈리에 커뮤니티

**데이터 수집 가능성:**
- ❓ **API 여부**: 확인 필요
- 🔍 **웹 스크레이핑**: 가능성 있음 (와인별 리뷰 페이지)
- 📊 **데이터 유형**: Consumer ratings, Tasting notes

**신뢰도 평가:**
- Trust Tier: T4_community (사용자 생성 콘텐츠)
- Collection Tier: C3_html_js 또는 C4_api (확인 필요)
- Purpose Tags: P3_investment (소비자 평가), P4_trend_discovery

**우선순위**: Phase 3 (Consumer rating platform 통합 시)

### 2. CellarTracker
**설명**: 1,300만 개 리뷰 데이터베이스 보유

**주요 기능:**
- 방대한 사용자 리뷰 DB (13 million reviews)
- 와인 추천 시스템
- 셀러 관리 (개인 와인 컬렉션)

**데이터 수집 가능성:**
- ✅ **API 여부**: CellarTracker API 존재 (확인됨)
- 🔍 **웹 스크레이핑**: robots.txt 확인 필요
- 📊 **데이터 유형**: User reviews, Ratings, Drinking windows

**신뢰도 평가:**
- Trust Tier: T4_community (사용자 생성 콘텐츠, 단 대규모 DB로 신뢰도 상승)
- Collection Tier: C4_api (API 제공)
- Purpose Tags: P3_investment (숙성 정보), P4_trend_discovery (소비자 선호도)

**통합 가치:**
- **매우 높음** - 1,300만 리뷰는 Vivino 다음으로 큰 규모
- Drinking window 정보는 투자 판단에 핵심
- API 제공으로 수집 용이

**우선순위**: Phase 3 (Consumer rating 최우선 후보)

### 3. Wine-Searcher
**설명**: 빠른 검색 및 평론가 점수 확인 기능

**주요 기능:**
- 와인 검색 엔진
- 평론가 점수 통합 (Wine Spectator, Parker 등)
- 가격 비교 (Price comparison across retailers)

**데이터 수집 가능성:**
- ❓ **API 여부**: 상업용 API 가능성 (확인 필요)
- 🔍 **웹 스크레이핑**: 복잡 (JS 기반)
- 📊 **데이터 유형**: Expert scores aggregation, Price trends

**신뢰도 평가:**
- Trust Tier: T2_expert (전문가 점수 통합) / T4_community (가격 정보)
- Collection Tier: C3_html_js 또는 C5_manual (페이월 가능성)
- Purpose Tags: P3_investment (가격 트렌드), P2_market_analysis

**통합 가치:**
- **높음** - 전문가 점수 통합 플랫폼으로 유용
- 가격 트렌드는 시장 분석에 활용 가능
- 단, 상업적 서비스로 접근성 제한 가능

**우선순위**: Phase 3 (Expert score aggregation)

**대안**: Wine-Searcher 대신 개별 출처(Parker, Spectator) 직접 수집 권장

### 4. Hello Vino: Wine Assistant App
**설명**: 음식-와인 페어링 및 라벨 평점 기능

**주요 기능:**
- Food & Wine Pairings
- 와인 라벨 스캐닝
- 추천 시스템

**데이터 수집 가능성:**
- ❌ **API 여부**: 없음 (모바일 앱 전용)
- 🔍 **웹 스크레이핑**: 어려움 (앱 기반)
- 📊 **데이터 유형**: Pairing recommendations

**신뢰도 평가:**
- Trust Tier: T4_community
- Collection Tier: C5_manual (앱 전용)
- Purpose Tags: P5_education (페어링 정보)

**통합 가치:**
- **낮음** - 모바일 앱 전용으로 수집 어려움
- 페어링 정보는 다른 출처에서도 확보 가능

**우선순위**: 제외 권장 (수집 불가)

### 5. Preferabli
**설명**: 1:1 특허 개인화 추천 시스템

**주요 기능:**
- AI 기반 개인화 (Patented personalization)
- 와인 추천
- 취향 프로파일링

**데이터 수집 가능성:**
- ❌ **API 여부**: 상업용 API (유료)
- 🔍 **웹 스크레이핑**: 불가 (개인화 콘텐츠)
- 📊 **데이터 유형**: Personalized recommendations

**신뢰도 평가:**
- Trust Tier: T3_professional (AI 기반 전문 서비스)
- Collection Tier: C5_manual (상업 서비스)
- Purpose Tags: P4_trend_discovery

**통합 가치:**
- **낮음** - 개인화 서비스로 공개 데이터 없음
- 상업적 파트너십 필요

**우선순위**: 제외 권장 (접근 불가)

## 통합 우선순위 매트릭스

| 플랫폼 | 신뢰도 | 수집 가능성 | 데이터 가치 | 종합 점수 | 우선순위 |
|-------|-------|-----------|-----------|----------|---------|
| **CellarTracker** | 0.75 | 0.90 (API) | 0.95 (1,300만 리뷰) | **0.86** | **1위** |
| **Wine-Searcher** | 0.85 | 0.50 (복잡) | 0.80 (전문가 통합) | **0.72** | 2위 |
| **Delectable Wine** | 0.70 | 0.70 (HTML) | 0.75 (소비자 평가) | **0.72** | 3위 |
| **Hello Vino** | 0.65 | 0.20 (앱 전용) | 0.60 (페어링) | **0.48** | 제외 |
| **Preferabli** | 0.80 | 0.30 (유료) | 0.70 (AI 추천) | **0.60** | 제외 |

**계산식**: `(신뢰도 × 0.4) + (수집 가능성 × 0.35) + (데이터 가치 × 0.25)`

## 통합 권장안

### Phase 3 우선순위 1: CellarTracker

**통합 가치:**
- ✅ 1,300만 리뷰 (Vivino 다음 규모)
- ✅ API 제공 (수집 용이)
- ✅ Drinking window 정보 (투자 판단 핵심)
- ✅ 커뮤니티 신뢰도 높음 (와인 애호가 중심)

**sources.yaml 추가안:**
```yaml
- name: "CellarTracker"
  id: "consumer_cellartracker_global"
  type: "community"
  country: "US"
  continent: "NEW_WORLD"
  region: "Americas/North/USA"

  # 신뢰도 분류
  trust_tier: "T4_community"  # 사용자 생성 콘텐츠 (단, 대규모 DB)
  collection_tier: "C4_api"  # API 제공
  purpose_tags: ["P3_investment", "P4_trend_discovery"]

  tier: "community"
  content_type: "consumer_rating"
  language: "en"
  enabled: false  # Phase 3에서 활성화
  weight: 2.0
  supports_rss: false
  requires_login: true  # API 키 필요
  notes: "13 million user reviews, drinking windows, API available"

  config:
    api_url: "https://www.cellartracker.com/api/"
    collection_method: "api"
    rate_limit: "60 requests/minute"
    ethical_constraint: "Respect API terms, cite CellarTracker as source"
```

**구현 작업:**
1. CellarTracker API 문서 확인
2. API 키 발급 (무료 tier 확인)
3. `collectors/api_collector.py` 구현
4. Rate limiting 준수 (60 req/min)
5. Drinking window 데이터 스키마 확장

**예상 신뢰도**: 0.75 (B 등급) - 소비자 콘텐츠이나 규모와 커뮤니티 품질로 보정

### Phase 3 우선순위 2: Wine-Searcher (조건부)

**통합 가치:**
- ✅ 전문가 점수 통합 (Parker, Spectator, Suckling 등)
- ✅ 가격 트렌드 (투자 분석용)
- ⚠️ 상업 서비스 (접근 제한 가능)
- ⚠️ 복잡한 수집 (JS 기반)

**대안 전략:**
- Wine-Searcher 대신 **개별 출처 직접 수집 권장**
  1. Robert Parker/Wine Advocate
  2. James Suckling
  3. Jancis Robinson
  4. Antonio Galloni (Vinous)

**조건부 추가:**
- 무료 API 또는 공개 콘텐츠 확인 후 결정
- 페이월 있으면 제외

### Phase 3 우선순위 3: Delectable Wine (검토)

**통합 가치:**
- ✅ 소믈리에 커뮤니티 (전문성 높음)
- ✅ 이미지 인식 데이터 (와인 트렌드)
- ⚠️ 수집 복잡도 중간

**추가 조사 필요:**
- 웹사이트 구조 확인
- robots.txt 확인
- API 제공 여부 확인

**조건부 추가:**
- HTML 스크레이핑 가능 시 Phase 3에서 고려

## 기존 Rating Platforms와 비교

### Vivino vs CellarTracker

| 항목 | Vivino | CellarTracker |
|-----|--------|---------------|
| 리뷰 수 | ~5,000만 (추정) | 1,300만 |
| 사용자 층 | 일반 소비자 | 와인 애호가 |
| 데이터 품질 | 중간 (대중적) | 높음 (전문성) |
| API | ❌ (제한적) | ✅ (제공) |
| Drinking Window | ❌ | ✅ (핵심 기능) |
| 수집 난이도 | 높음 (C3_html_js) | 중간 (C4_api) |

**권장**: Vivino + CellarTracker 병행 수집
- Vivino: 대중 트렌드 (P4_trend_discovery)
- CellarTracker: 투자 판단 (P3_investment)

### Wine-Searcher vs 개별 전문가 출처

| 항목 | Wine-Searcher | Parker + Spectator + Suckling |
|-----|---------------|------------------------------|
| 전문가 점수 통합 | ✅ (한 곳에서) | ✅ (개별 수집) |
| 가격 트렌드 | ✅ | ❌ |
| 수집 난이도 | 높음 (상업 서비스) | 중간-높음 (페이월) |
| 신뢰도 | 0.85 (T2) | 0.95 (T2, 직접 출처) |
| 비용 | 유료 가능성 | 무료/유료 혼재 |

**권장**: 개별 전문가 출처 우선 수집
- 더 높은 신뢰도 (1차 출처)
- Wine-Searcher는 가격 트렌드 전용으로 고려

## sources.yaml 업데이트 제안

### 즉시 추가 (Phase 3 대비)

```yaml
# Phase 3: Consumer Rating Platforms

- name: "CellarTracker"
  id: "consumer_cellartracker_global"
  type: "community"
  country: "US"
  continent: "NEW_WORLD"
  region: "Americas/North/USA"
  trust_tier: "T4_community"
  collection_tier: "C4_api"
  purpose_tags: ["P3_investment", "P4_trend_discovery"]
  tier: "community"
  content_type: "consumer_rating"
  language: "en"
  enabled: false
  weight: 2.0
  supports_rss: false
  requires_login: true
  notes: "13M reviews, drinking windows, API available"
  config:
    api_url: "https://www.cellartracker.com/api/"
    collection_method: "api"

- name: "Vivino"
  id: "consumer_vivino_global"
  type: "community"
  country: "DK"
  continent: "OLD_WORLD"
  region: "Europe/Northern/Denmark"
  trust_tier: "T4_community"
  collection_tier: "C3_html_js"
  purpose_tags: ["P4_trend_discovery"]
  tier: "community"
  content_type: "consumer_rating"
  language: "en"
  enabled: false
  weight: 1.8
  supports_rss: false
  requires_login: false
  notes: "50M+ reviews, mass consumer trends, JS rendering needed"
  config:
    list_url: "https://www.vivino.com/explore"
    collection_method: "html"
```

### 검토 후 추가 (Phase 3 후반)

```yaml
# 조건부 추가 (API/접근성 확인 후)

- name: "Delectable Wine"
  id: "consumer_delectable_global"
  type: "community"
  country: "US"
  continent: "NEW_WORLD"
  region: "Americas/North/USA"
  trust_tier: "T4_community"
  collection_tier: "C3_html_js"
  purpose_tags: ["P3_investment", "P4_trend_discovery"]
  tier: "community"
  content_type: "consumer_rating"
  language: "en"
  enabled: false
  weight: 1.9
  supports_rss: false
  requires_login: false
  notes: "Sommelier community, image recognition, HTML scraping needed (TBD)"
  config:
    list_url: "https://delectable.com/"
    collection_method: "html"
```

## 윤리적 수집 가이드라인

### CellarTracker API 사용 시

1. **API 이용 약관 준수**
   - Rate limiting: 60 req/min 엄수
   - API 키 보안 (환경 변수 저장)
   - 상업적 재판매 금지

2. **출처 표시**
   - 모든 데이터에 "Source: CellarTracker" 명시
   - 사용자 리뷰는 익명화 유지
   - URL 링크백 제공

3. **데이터 사용 제한**
   - 분석/트렌드 파악 목적만
   - 개인 정보 수집 금지
   - 리뷰 전문 복사 최소화 (요약만)

### HTML 스크레이핑 시 (Vivino, Delectable)

1. **robots.txt 준수**
   - User-Agent 명시: "WineRadar/1.0 (Research Bot)"
   - Disallow 경로 존중
   - Crawl-delay 준수 (최소 5초)

2. **Rate Limiting**
   - 최소 5초 간격
   - 동시 요청 1개로 제한
   - 피크 시간대 회피 (현지 시간 오전 2-6시 권장)

3. **콘텐츠 사용**
   - 평점/점수만 수집 (리뷰 전문 X)
   - 통계 목적으로만 사용
   - 출처 명시 및 링크 제공

## 구현 로드맵

### Phase 3-A: API 기반 수집 (CellarTracker)

**작업 순서:**
1. CellarTracker API 문서 리뷰
2. API 키 발급 (무료/유료 tier 확인)
3. `collectors/api_collector.py` 구현
   ```python
   class APICollector(BaseCollector):
       def __init__(self, api_key: str, rate_limit: int = 60):
           self.api_key = api_key
           self.rate_limiter = RateLimiter(rate_limit, 60)  # 60 req/min

       def fetch_reviews(self, wine_id: str) -> list[dict]:
           # API 호출 로직
           pass
   ```
4. DuckDB 스키마 확장
   ```sql
   ALTER TABLE urls ADD COLUMN drinking_window_start INTEGER;
   ALTER TABLE urls ADD COLUMN drinking_window_end INTEGER;
   ALTER TABLE urls ADD COLUMN user_rating_avg DOUBLE;
   ALTER TABLE urls ADD COLUMN user_rating_count INTEGER;
   ```
5. 테스트 (10개 와인으로 시작)
6. 점진적 확장 (1,000 → 10,000 → 전체)

**예상 소요 시간**: 2-3주

### Phase 3-B: JS 렌더링 수집 (Vivino)

**작업 순서:**
1. Playwright 통합 (`collectors/js_scraper.py`)
2. Vivino 페이지 구조 분석
3. CSS selector 매핑
4. 헤드리스 브라우저 자동화
5. 오류 처리 (CAPTCHA 대응)

**예상 소요 시간**: 3-4주

### Phase 3-C: 검토 플랫폼 (Delectable, Wine-Searcher)

**작업 순서:**
1. 접근성 조사 (API/HTML 가능성)
2. 윤리적 수집 가능 여부 판단
3. 조건부 구현

**예상 소요 시간**: 2주 (조사) + 구현 (TBD)

## 데이터 활용 시나리오

### Scenario 1: 투자 등급 분석 (P3_investment)

**사용 데이터:**
- CellarTracker Drinking Window (2025-2035)
- Wine Spectator Expert Score (95점)
- Vivino Consumer Rating (4.5/5)

**분석 로직:**
```python
def calculate_investment_grade(wine: dict) -> str:
    expert_score = wine.get("expert_score", 0)  # Wine Spectator
    consumer_rating = wine.get("consumer_rating", 0)  # Vivino/CellarTracker
    drinking_window = wine.get("drinking_window_start", 0)

    # 전문가 점수 가중치 70%
    expert_weight = expert_score / 100 * 0.7

    # 소비자 평가 가중치 20%
    consumer_weight = consumer_rating / 5 * 0.2

    # 숙성 가능성 가중치 10%
    years_to_peak = drinking_window - current_year
    aging_weight = min(years_to_peak / 10, 1.0) * 0.1

    investment_score = expert_weight + consumer_weight + aging_weight

    if investment_score >= 0.9:
        return "A+ (Strong Buy)"
    elif investment_score >= 0.8:
        return "A (Buy)"
    elif investment_score >= 0.7:
        return "B (Hold)"
    else:
        return "C (Sell)"
```

### Scenario 2: 소비자 vs 전문가 평가 괴리 분석

**목적**: 저평가 와인 발굴

**데이터:**
- Expert Score (Parker, Spectator): 85점
- Consumer Rating (Vivino, CellarTracker): 4.3/5 (86점 환산)

**괴리도 계산:**
```python
def find_undervalued_wines(db_path: Path) -> list[dict]:
    """전문가 점수는 낮지만 소비자 평가는 높은 와인 (가성비 와인)"""
    query = """
    SELECT
        title,
        expert_score,
        consumer_rating * 20 AS consumer_score_100,
        (consumer_rating * 20 - expert_score) AS score_gap
    FROM urls
    WHERE
        expert_score < 90
        AND consumer_rating >= 4.2
        AND score_gap > 5
    ORDER BY score_gap DESC
    LIMIT 20
    """
    return execute_query(db_path, query)
```

### Scenario 3: 트렌드 감지 (P4_trend_discovery)

**목적**: 급부상하는 와인/지역 감지

**데이터:**
- Vivino 검색량 증가율
- CellarTracker 리뷰 증가 추세
- 소셜 미디어 멘션 (향후)

**구현:**
```python
def detect_trending_wines(db_path: Path, time_window: timedelta) -> list[dict]:
    """최근 N일간 리뷰 증가율 Top 20"""
    query = """
    SELECT
        title,
        country,
        grape_variety,
        COUNT(*) as review_count,
        AVG(consumer_rating) as avg_rating,
        COUNT(*) / (SELECT COUNT(*) FROM urls WHERE published_at < :start_date) AS growth_rate
    FROM urls
    WHERE published_at >= :start_date
    GROUP BY title, country, grape_variety
    ORDER BY growth_rate DESC
    LIMIT 20
    """
    return execute_query(db_path, query, {"start_date": datetime.now() - time_window})
```

## 결론 및 권장사항

### 핵심 발견

1. **CellarTracker는 즉시 통합 가치 높음**
   - API 제공으로 수집 용이
   - 1,300만 리뷰 (Vivino 다음 규모)
   - Drinking window 정보 (투자 판단 핵심)

2. **Wine-Searcher는 대안 고려 필요**
   - 상업 서비스로 접근 제한 가능
   - 개별 전문가 출처 직접 수집 권장

3. **Vivino는 필수이나 수집 난이도 높음**
   - JS 렌더링 필요 (Playwright)
   - Phase 3에서 Wine Australia와 함께 구현

4. **Hello Vino, Preferabli는 제외**
   - 모바일 앱 전용 또는 상업 서비스
   - 수집 불가 또는 비용 대비 가치 낮음

### 즉시 실행 가능한 액션

1. **sources.yaml에 CellarTracker, Vivino 추가**
2. **CellarTracker API 문서 확인 및 키 발급**
3. **Phase 3 구현 계획 수립**:
   - 3-A: CellarTracker API (2-3주)
   - 3-B: Vivino + Wine Australia JS 렌더링 (3-4주)
   - 3-C: Delectable 조사 (2주)

### 최종 평가

**Consumer platform 통합으로 WineRadar의 데이터 다양성이 크게 향상됩니다:**

- **현재 (Phase 1-2)**: 전문가/공식 기관 출처 (18개, A 등급 이상)
- **Phase 3 추가**: 소비자 평가 플랫폼 (2-3개)
- **효과**: 전문가 vs 소비자 괴리 분석, 투자 등급 정교화, 트렌드 감지 정확도 상승

**CellarTracker는 Phase 3 최우선 순위로 권장합니다.**
