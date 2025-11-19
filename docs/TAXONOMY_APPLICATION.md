# 최종 분류체계 적용 결과 (Taxonomy Application Results)

## 개요

sources.yaml의 전체 21개 소스에 최종 분류체계를 적용했습니다.

**적용된 필드:**
- `trust_tier`: T1_authoritative / T2_expert / T3_professional / T4_community
- `collection_tier`: C1_rss / C2_html_simple / C3_html_js / C4_api / C5_manual
- `purpose_tags`: Array of P1-P5 values

## 분류 결과 통계

### Trust Tier 분포

| Trust Tier | 소스 수 | 비율 | 대표 소스 |
|-----------|---------|------|----------|
| **T1_authoritative** | 14 | 66.7% | Wine Institute, Wine Australia, Korean Wine Consumer Association |
| **T2_expert** | 4 | 19.0% | Decanter, Gambero Rosso, La Revue du vin de France, Wine Spectator |
| **T3_professional** | 3 | 14.3% | Wine21, Wine Review, Shinsegae L&B |
| **T4_community** | 0 | 0% | - |

**분석:** 공식 기관이 2/3를 차지하며 신뢰도 높은 출처 중심으로 구성되어 있습니다.

### Collection Tier 분포

| Collection Tier | 소스 수 | 비율 | 구현 난이도 |
|----------------|---------|------|------------|
| **C1_rss** | 2 | 9.5% | 즉시 구현 가능 ✅ |
| **C2_html_simple** | 17 | 81.0% | Phase 2 구현 (BeautifulSoup) |
| **C3_html_js** | 1 | 4.8% | Phase 3 구현 (Selenium/Playwright) |
| **C4_api** | 0 | 0% | - |
| **C5_manual** | 1 | 4.8% | 페이월, 수동 수집만 가능 |

**분석:**
- 즉시 사용 가능한 RSS는 2개 (9.5%)
- 대부분 (81%) HTML 스크레이핑 필요
- JS 렌더링이 필요한 고난이도 출처 1개 (Wine Australia)

### Purpose Tags 분포

| Purpose | 소스 수 | 사용 사례 |
|---------|---------|----------|
| **P1_daily_briefing** | 6 | 일일 브리핑 (Decanter, Gambero Rosso, La Revue, Wine21, Wine Review) |
| **P2_market_analysis** | 9 | 시장 분석 (Wine Institute, Wine Australia, IFV, ICEX, Wines of Chile/Argentina) |
| **P3_investment** | 1 | 투자 의사결정 (Wine Spectator) |
| **P4_trend_discovery** | 6 | 트렌드 발견 (Premium media + Shinsegae L&B) |
| **P5_education** | 8 | 교육 자료 (Federdoc, Wines of Germany/Portugal/New Zealand/South Africa, Korean Wine Consumer Association) |

**분석:**
- 시장 분석 목적 출처가 가장 많음 (9개)
- 일일 브리핑과 트렌드 발견용 프리미엄 미디어 6개
- 교육 자료 8개로 지식 베이스 구축 가능

## 우선순위 매트릭스 결과

**우선순위 공식:**
```
Priority Score = (trust_weight × 0.4) + (collection_ease × 0.35) + (user_value × 0.25)
```

**가중치 매핑:**
- Trust: T1=1.0, T2=0.95, T3=0.85, T4=0.70
- Collection: C1=1.0, C2=0.85, C3=0.70, C4=0.90, C5=0.30
- User Value: High=1.0, Medium=0.75, Low=0.50 (purpose_tags 수 기반)

### Top 10 우선순위 순위

| 순위 | 소스 | Trust | Collection | Purpose | 우선순위 점수 | Phase |
|-----|------|-------|-----------|---------|------------|-------|
| 1 | **Decanter** | T2_expert | C1_rss | P1, P4 | 0.975 | **Phase 1** ✅ |
| 2 | **Gambero Rosso** | T2_expert | C1_rss | P1, P4 | 0.975 | **Phase 1** ✅ |
| 3 | **Wine Institute** | T1_authoritative | C2_html_simple | P2 | 0.838 | **Phase 2** 🔄 |
| 4 | **IFV (France)** | T1_authoritative | C2_html_simple | P2, P5 | 0.856 | **Phase 2** 🔄 |
| 5 | **Wine21** | T3_professional | C2_html_simple | P1, P4 | 0.850 | **Phase 2** 🔄 |
| 6 | **Wine Review** | T3_professional | C2_html_simple | P1, P4 | 0.850 | **Phase 2** 🔄 |
| 7 | **La Revue du vin de France** | T2_expert | C2_html_simple | P1, P4 | 0.869 | Phase 2 |
| 8 | **Wines of Chile** | T1_authoritative | C2_html_simple | P2 | 0.838 | Phase 2 |
| 9 | **Wines of Argentina** | T1_authoritative | C2_html_simple | P2 | 0.838 | Phase 2 |
| 10 | **Wine Australia** | T1_authoritative | C3_html_js | P2 | 0.745 | **Phase 3** ⏳ |

### Phase별 구현 계획

#### Phase 1: RSS 기반 즉시 구현 (2개)
**목표:** MVP 파이프라인 구축

1. **Decanter** (media_decanter_global)
   - Trust: T2_expert (국제적 권위)
   - Collection: C1_rss ✅
   - Purpose: P1_daily_briefing, P4_trend_discovery
   - URL: https://www.decanter.com/feed/
   - 우선순위: 0.975

2. **Gambero Rosso** (media_gambero_it)
   - Trust: T2_expert (이탈리아 권위)
   - Collection: C1_rss ✅
   - Purpose: P1_daily_briefing, P4_trend_discovery
   - URL: https://www.gamberorosso.it/feed/
   - 우선순위: 0.975

**구현 작업:**
- [ ] `collectors/rss_collector.py` 구현
- [ ] RSS 파서 (feedparser) 통합
- [ ] RawItem 생성 로직 (새 필드 포함)
- [ ] DuckDB 저장 테스트
- [ ] 매일 자동 수집 스케줄러 설정

#### Phase 2: HTML 스크레이핑 (6-8개)
**목표:** 핵심 소스 확장

**우선순위 높음 (4개):**
1. **Wine Institute** (US) - 통계/시장 분석
2. **IFV** (France) - 통계/교육
3. **Wine21** (Korea) - 일일 브리핑
4. **Wine Review** (Korea) - 일일 브리핑

**추가 고려 (4개):**
5. La Revue du vin de France (프랑스 프리미엄)
6. Wines of Chile (시장 리포트)
7. Wines of Argentina (시장 리포트)
8. ICEX (스페인 시장 리포트)

**구현 작업:**
- [ ] `collectors/html_scraper.py` 프레임워크
- [ ] BeautifulSoup 기반 파서
- [ ] 소스별 CSS selector 매핑
- [ ] robots.txt 준수 및 rate limiting (5초 간격)
- [ ] 오류 처리 및 재시도 로직

#### Phase 3: 고급 수집 (2개)
**목표:** JS 렌더링 및 API 통합

1. **Wine Australia** (C3_html_js)
   - Selenium/Playwright 필요
   - 호주 시장 통계 (중요도 높음)

2. **Wine Spectator** (C5_manual)
   - 페이월 제한
   - 공개 콘텐츠만 수집
   - 전문가 평점 (투자 분석용)

**구현 작업:**
- [ ] Playwright 통합 (Wine Australia)
- [ ] 윤리적 수집 프레임워크 (페이월 존중)
- [ ] 수동 입력 인터페이스 (Wine Spectator 공개 콘텐츠)

## 대륙별 분포

### 구대륙 (OLD_WORLD): 10개

| 국가 | 소스 수 | Trust Tier | Collection Tier |
|-----|---------|-----------|----------------|
| 🇬🇧 GB | 1 | T2_expert | C1_rss ✅ |
| 🇫🇷 FR | 2 | T1, T2 | C2_html_simple |
| 🇮🇹 IT | 2 | T1, T2 | C1_rss, C2_html_simple |
| 🇪🇸 ES | 1 | T1 | C2_html_simple |
| 🇩🇪 DE | 1 | T1 | C2_html_simple |
| 🇵🇹 PT | 1 | T1 | C2_html_simple |

**특징:**
- RSS 가능: 2개 (Decanter, Gambero Rosso)
- 공식 기관 다수 (프랑스 IFV, 이탈리아 Federdoc 등)
- 다국어 처리 필요 (프랑스어, 이탈리아어, 스페인어, 독일어)

### 신대륙 (NEW_WORLD): 7개

| 국가 | 소스 수 | Trust Tier | Collection Tier |
|-----|---------|-----------|----------------|
| 🇺🇸 US | 2 | T1, T2 | C2_html_simple, C5_manual |
| 🇦🇺 AU | 1 | T1 | C3_html_js |
| 🇳🇿 NZ | 1 | T1 | C2_html_simple |
| 🇨🇱 CL | 1 | T1 | C2_html_simple |
| 🇦🇷 AR | 1 | T1 | C2_html_simple |
| 🇿🇦 ZA | 1 | T1 | C2_html_simple |

**특징:**
- RSS 없음 (0%)
- 모두 공식 기관 (T1) 또는 전문가 매체 (T2)
- Wine Australia는 JS 렌더링 필요 (C3_html_js)
- 영어 콘텐츠 중심

### 아시아 (ASIA): 4개

| 국가 | 소스 수 | Trust Tier | Collection Tier |
|-----|---------|-----------|----------------|
| 🇰🇷 KR | 4 | T1, T3 (×3) | C2_html_simple (전체) |

**특징:**
- RSS 없음 (0%)
- 한국 전문 미디어 2개 (Wine21, Wine Review)
- 공식 협회 1개 (Korean Wine Consumer Association)
- 주요 유통사 1개 (Shinsegae L&B)
- 한국어 NLP 처리 필요 (KoNLPy)

## 목적별 사용 시나리오

### Scenario 1: 일일 브리핑 (P1_daily_briefing)
**사용 소스 (6개):**
- Decanter ✅ (RSS)
- Gambero Rosso ✅ (RSS)
- La Revue du vin de France (HTML)
- Wine21 (HTML)
- Wine Review (HTML)
- (추가: Shinsegae L&B for local trends)

**구현:**
```python
from graph.graph_queries import get_view
from datetime import timedelta

# 24시간 이내 뉴스만
briefing = get_view(
    db_path,
    view_type="purpose",
    focus_id="P1_daily_briefing",
    time_window=timedelta(days=1),
    limit=20
)
```

### Scenario 2: 시장 분석 리포트 (P2_market_analysis)
**사용 소스 (9개):**
- Wine Institute (US statistics)
- Wine Australia (AU statistics)
- IFV (France statistics)
- ICEX (Spain market report)
- Wines of Chile/Argentina (market reports)

**구현:**
```python
# 30일 이내 통계/리포트
market_report = get_view(
    db_path,
    view_type="purpose",
    focus_id="P2_market_analysis",
    time_window=timedelta(days=30),
    source_filter=["content_type=statistics", "content_type=market_report"],
    limit=50
)
```

### Scenario 3: 투자 등급 분석 (P3_investment)
**사용 소스 (1개 + 향후 확장):**
- Wine Spectator (전문가 평점)
- (Phase 3 추가: Robert Parker, James Suckling)

**구현:**
```python
# 180일 이내 전문가 평가
investment_grades = get_view(
    db_path,
    view_type="purpose",
    focus_id="P3_investment",
    time_window=timedelta(days=180),
    source_filter=["trust_tier=T2_expert"],
    limit=100
)
```

### Scenario 4: 트렌드 발견 (P4_trend_discovery)
**사용 소스 (6개):**
- Premium media (Decanter, Gambero Rosso, La Revue, Wine21, Wine Review)
- Importer news (Shinsegae L&B)

**구현:**
```python
# 14일 이내 트렌드
trends = get_view(
    db_path,
    view_type="purpose",
    focus_id="P4_trend_discovery",
    time_window=timedelta(days=14),
    source_filter=["trust_tier=T2_expert", "trust_tier=T3_professional"],
    limit=30
)
```

### Scenario 5: 교육 자료 (P5_education)
**사용 소스 (8개):**
- 공식 협회 (Federdoc, Wines of Germany/Portugal/NZ/South Africa)
- 연구기관 (IFV)
- 소비자 협회 (Korean Wine Consumer Association)

**구현:**
```python
# Evergreen 콘텐츠 (시간 가중치 낮음)
education = get_view(
    db_path,
    view_type="purpose",
    focus_id="P5_education",
    time_window=timedelta(days=365),  # 1년
    source_filter=["content_type=education"],
    limit=100
)
```

## 다음 단계

### 즉시 구현 (Phase 1)
1. **RSS Collector 구현**
   - 파일: `collectors/rss_collector.py`
   - 대상: Decanter, Gambero Rosso
   - 예상 작업 시간: 4-6시간

2. **DuckDB 스키마 확인**
   - 새 필드 (trust_tier, collection_tier, purpose_tags) 컬럼 추가
   - 마이그레이션 스크립트 작성

3. **기본 파이프라인 테스트**
   - 수집 → 저장 → 조회 전 과정 검증
   - View 쿼리 테스트

### 중기 목표 (Phase 2)
1. **HTML Scraper 프레임워크**
   - 파일: `collectors/html_scraper.py`
   - 우선순위: Wine Institute, Wine21, Wine Review, IFV

2. **다국어 NLP**
   - KoNLPy (한국어)
   - spaCy (프랑스어, 이탈리아어)

3. **소스 4-8개 추가**
   - 총 10-12개 소스 운영

### 장기 목표 (Phase 3)
1. **JS 렌더링 (Wine Australia)**
2. **Rating Platform 통합** (Vivino API 고려)
3. **100+ 소스로 확장**

## 결론

**현재 상태:**
- 21개 소스 정의 완료 ✅
- 최종 분류체계 적용 완료 ✅
- RSS 작동 확인 (2개) ✅
- 우선순위 매트릭스 완성 ✅

**즉시 실행 가능:**
- Phase 1 RSS Collector 구현으로 MVP 파이프라인 구축
- Decanter + Gambero Rosso로 일일 브리핑 시작

**확장 가능성:**
- HTML Scraper 프레임워크로 17개 소스 추가 가능
- 목적별 View로 다양한 사용 사례 지원
- 신뢰도/편의성/사용자 관점을 모두 고려한 체계적 확장

이제 **데이터 소스의 신뢰성, 편의성, 사용자의 뷰를 고려한 분류 체계**가 완성되었습니다.
