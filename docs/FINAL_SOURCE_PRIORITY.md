# 최종 소스 우선순위 확정 (Final Source Priority)

## 우선순위 결정 기준

### 종합 점수 계산식
```
Priority Score = (Reliability × 0.40) + (Accessibility × 0.35) + (User_Value × 0.25)
```

**세부 가중치:**
1. **Reliability (신뢰도)**: 0.40
   - T1_authoritative: 1.0
   - T2_expert: 0.95
   - T3_professional: 0.85
   - T4_community: 0.70

2. **Accessibility (접근성)**: 0.35
   - C1_rss: 1.0 (즉시 사용 가능)
   - C2_html_simple: 0.85 (BeautifulSoup)
   - C3_html_js: 0.70 (Playwright)
   - C4_api: 0.90 (API 제공)
   - C5_manual: 0.30 (수동 수집)

3. **User_Value (사용자 가치)**: 0.25
   - P1_daily_briefing: 1.0 (높음)
   - P2_market_analysis: 0.95 (높음)
   - P3_investment: 0.90 (중간-높음)
   - P4_trend_discovery: 0.85 (중간)
   - P5_education: 0.60 (낮음)

## 최종 우선순위 순위 (Top 15)

| 순위 | 소스 | Reliability | Accessibility | User Value | **종합 점수** | Phase |
|-----|------|------------|--------------|-----------|------------|-------|
| **1** | **Decanter** | 0.95 (T2) | 1.0 (C1) | 0.93 (P1,P4) | **0.956** | **Phase 1** ✅ |
| **2** | **Gambero Rosso** | 0.95 (T2) | 1.0 (C1) | 0.93 (P1,P4) | **0.956** | **Phase 1** ✅ |
| **3** | **Wine Institute** | 1.0 (T1) | 0.85 (C2) | 0.95 (P2) | **0.938** | **Phase 2** 🔄 |
| **4** | **IFV (France)** | 1.0 (T1) | 0.85 (C2) | 0.78 (P2,P5) | **0.918** | **Phase 2** 🔄 |
| **5** | **Wines of Chile** | 1.0 (T1) | 0.85 (C2) | 0.95 (P2) | **0.938** | Phase 2 |
| **6** | **Wines of Argentina** | 1.0 (T1) | 0.85 (C2) | 0.95 (P2) | **0.938** | Phase 2 |
| **7** | **ICEX (Spain)** | 1.0 (T1) | 0.85 (C2) | 0.95 (P2) | **0.938** | Phase 2 |
| **8** | **La Revue du vin de France** | 0.95 (T2) | 0.85 (C2) | 0.93 (P1,P4) | **0.918** | Phase 2 |
| **9** | **Wine21** | 0.85 (T3) | 0.85 (C2) | 0.93 (P1,P4) | **0.873** | **Phase 2** 🔄 |
| **10** | **Wine Review** | 0.85 (T3) | 0.85 (C2) | 0.93 (P1,P4) | **0.873** | **Phase 2** 🔄 |
| **11** | **Federdoc** | 1.0 (T1) | 0.85 (C2) | 0.60 (P5) | **0.848** | Phase 2 |
| **12** | **Wines of Germany** | 1.0 (T1) | 0.85 (C2) | 0.60 (P5) | **0.848** | Phase 2 |
| **13** | **Wines of Portugal** | 1.0 (T1) | 0.85 (C2) | 0.60 (P5) | **0.848** | Phase 2 |
| **14** | **Wine Australia** | 1.0 (T1) | 0.70 (C3) | 0.95 (P2) | **0.883** | **Phase 3** ⏳ |
| **15** | **Korean Wine Consumer Assoc** | 1.0 (T1) | 0.85 (C2) | 0.60 (P5) | **0.848** | Phase 2 |

## Phase별 확정 소스

### Phase 1: 즉시 구현 (2개) ✅

**목표**: MVP 파이프라인 구축 (RSS 기반 일일 브리핑)

| # | 소스 | 점수 | 신뢰도 | 접근성 | 사용자 가치 | 확정 사유 |
|---|------|------|--------|--------|----------|----------|
| 1 | **Decanter** (GB) | 0.956 | T2_expert | C1_rss ✅ | P1, P4 | 국제 권위, RSS 작동 확인 |
| 2 | **Gambero Rosso** (IT) | 0.956 | T2_expert | C1_rss ✅ | P1, P4 | 이탈리아 권위, RSS 작동 확인 |

**구현 작업:**
- [x] RSS 피드 검증 완료
- [ ] `collectors/rss_collector.py` 구현
- [ ] DuckDB 스키마 메타 필드 추가
- [ ] 일일 수집 스케줄러 설정

**예상 완료**: 1-2주

### Phase 2: HTML 스크레이핑 확장 (8개) 🔄

**목표**: 핵심 출처 확보 (일일 브리핑 + 시장 분석)

**우선순위 높음 (4개):**

| # | 소스 | 점수 | 확정 사유 |
|---|------|------|----------|
| 3 | **Wine Institute** (US) | 0.938 | 미국 시장 통계 Gold Standard |
| 4 | **IFV** (France) | 0.918 | 학술 연구, 기후 데이터 |
| 9 | **Wine21** (Korea) | 0.873 | 한국 시장 필수 (일일 브리핑) |
| 10 | **Wine Review** (Korea) | 0.873 | 한국 시장 필수 (일일 브리핑) |

**추가 고려 (4개):**

| # | 소스 | 점수 | 확정 사유 |
|---|------|------|----------|
| 5 | **Wines of Chile** | 0.938 | 남미 시장 리포트 |
| 6 | **Wines of Argentina** | 0.938 | 남미 시장 리포트 |
| 7 | **ICEX** (Spain) | 0.938 | 스페인 수출 통계 |
| 8 | **La Revue du vin de France** | 0.918 | 프랑스 전문가 평가 |

**구현 작업:**
- [ ] `collectors/html_scraper.py` 프레임워크
- [ ] BeautifulSoup 기반 파서
- [ ] 소스별 CSS selector 매핑
- [ ] robots.txt 준수 및 rate limiting

**예상 완료**: 4-6주

### Phase 3: 고급 수집 (3개) ⏳

**목표**: JS 렌더링, Consumer Platform, Expert Rating

| # | 소스 | 점수 | Collection Tier | 확정 사유 |
|---|------|------|----------------|----------|
| 14 | **Wine Australia** (AU) | 0.883 | C3_html_js | 아시아-태평양 시장 (Playwright 필요) |
| - | **CellarTracker** (US) | 0.860 | C4_api | 1,300만 리뷰, Drinking Window |
| - | **Vivino** (DK) | 0.725 | C3_html_js | 5,000만 리뷰, 소비자 트렌드 |

**구현 작업:**
- [ ] Playwright 통합 (Wine Australia, Vivino)
- [ ] CellarTracker API 연동
- [ ] 윤리적 수집 프레임워크

**예상 완료**: 6-8주

## 제외/보류 소스 (8개)

| 소스 | 점수 | 제외 사유 |
|-----|------|----------|
| **Wine Spectator** | 0.690 | 페이월 (C5_manual), Phase 3 후반에 공개 콘텐츠만 수집 |
| **Shinsegae L&B** | 0.710 | 상업적 편향, 보조 지표로만 활용 |
| **New Zealand Wine** | 0.848 | 우선순위 낮음 (교육 자료), Phase 3 |
| **Wines of South Africa** | 0.848 | 우선순위 낮음 (교육 자료), Phase 3 |
| **Wines of Germany** | 0.848 | 우선순위 낮음 (교육 자료), Phase 3 |
| **Wines of Portugal** | 0.848 | 우선순위 낮음 (교육 자료), Phase 3 |
| **Federdoc** | 0.848 | 우선순위 낮음 (교육 자료), Phase 3 |
| **Hello Vino** | N/A | 모바일 앱 전용, 수집 불가 |
| **Preferabli** | N/A | 상업 서비스, 수집 불가 |

## 대륙별 확정 소스 분포

### Phase 1-2 (10개)

| 대륙 | 소스 수 | 대표 소스 | RSS |
|-----|---------|----------|-----|
| **OLD_WORLD** | 6 | Decanter, Gambero Rosso, La Revue, IFV, ICEX | 2개 ✅ |
| **NEW_WORLD** | 3 | Wine Institute, Wines of Chile/Argentina | 0개 |
| **ASIA** | 2 | Wine21, Wine Review | 0개 |

### Phase 3 추가 (3개)

| 대륙 | 소스 수 | 대표 소스 |
|-----|---------|----------|
| **NEW_WORLD** | 2 | Wine Australia, CellarTracker |
| **OLD_WORLD** | 1 | Vivino (Denmark) |

## Purpose별 확정 소스 분포

### P1_daily_briefing (일일 브리핑) - 6개

**Phase 1 (2개):**
- Decanter (RSS ✅)
- Gambero Rosso (RSS ✅)

**Phase 2 (4개):**
- La Revue du vin de France (HTML)
- Wine21 (HTML)
- Wine Review (HTML)

**효과**: 구대륙(3) + 아시아(2) 균형 있는 일일 뉴스 커버리지

### P2_market_analysis (시장 분석) - 6개

**Phase 2 (5개):**
- Wine Institute (US)
- IFV (France)
- Wines of Chile
- Wines of Argentina
- ICEX (Spain)

**Phase 3 (1개):**
- Wine Australia

**효과**: 주요 생산국 공식 통계 확보

### P3_investment (투자 분석) - 2개

**Phase 3 (2개):**
- CellarTracker (Drinking Window, 소비자 평가)
- Wine Spectator (전문가 평점, 공개 콘텐츠만)

### P4_trend_discovery (트렌드 발견) - 6개

**Phase 1-2 동일 (P1과 중복):**
- Decanter, Gambero Rosso, La Revue, Wine21, Wine Review

**Phase 3 추가:**
- Vivino (대중 트렌드)

### P5_education (교육 자료) - 8개 (Phase 3로 연기)

- IFV (France)
- Federdoc (Italy)
- Wines of Germany/Portugal/NZ/South Africa
- Korean Wine Consumer Association

## 최종 확정 로드맵

### 현재 상태 (2025-11-19)

✅ **완료:**
- 21개 소스 정의 및 분류체계 적용
- RSS 검증 완료 (2/21 작동 확인)
- 신뢰도 평가 완료
- 우선순위 매트릭스 완성

### Phase 1 목표 (1-2주)

**구현 소스**: 2개
- Decanter
- Gambero Rosso

**달성 효과:**
- 일일 브리핑 가능
- 구대륙 (영국, 이탈리아) 뉴스 커버
- RSS 기반 안정적 수집

**핵심 작업:**
1. `collectors/rss_collector.py` 구현
2. DuckDB 메타 필드 추가
3. 일일 스케줄러 설정

### Phase 2 목표 (4-6주)

**구현 소스**: 8개
- 우선순위 높음 (4개): Wine Institute, IFV, Wine21, Wine Review
- 추가 고려 (4개): Wines of Chile/Argentina, ICEX, La Revue

**달성 효과:**
- 일일 브리핑 6개 소스 (구대륙 4 + 아시아 2)
- 시장 분석 6개 소스 (미국, 프랑스, 스페인, 남미)
- 총 10개 소스 운영

**핵심 작업:**
1. HTML 스크레이퍼 프레임워크
2. CSS selector 매핑 (8개 소스)
3. robots.txt 준수, rate limiting

### Phase 3 목표 (6-8주)

**구현 소스**: 3개
- Wine Australia (JS 렌더링)
- CellarTracker (API)
- Vivino (JS 렌더링)

**달성 효과:**
- 아시아-태평양 시장 통계 (Wine Australia)
- 투자 분석 (CellarTracker Drinking Window)
- 소비자 트렌드 (Vivino 5,000만 리뷰)
- 총 13개 소스 운영

**핵심 작업:**
1. Playwright 통합
2. CellarTracker API 연동
3. 윤리적 수집 프레임워크

## 성공 기준 (KPI)

### Phase 1
- ✅ RSS 수집 성공률 > 95%
- ✅ 일일 뉴스 건수 > 10건
- ✅ 수집 실패 시 1시간 내 복구

### Phase 2
- ✅ HTML 수집 성공률 > 85%
- ✅ 일일 뉴스 건수 > 30건
- ✅ 시장 분석 리포트 월 1회 생성 가능
- ✅ 한국 시장 커버리지 > 50%

### Phase 3
- ✅ 전체 수집 성공률 > 80%
- ✅ Consumer rating 데이터 > 10,000건
- ✅ 투자 등급 분석 가능
- ✅ 대륙별 균형 (OLD_WORLD 40% + NEW_WORLD 40% + ASIA 20%)

## 결론

**최종 확정 소스: 13개 (3단계)**

**Phase별 분포:**
- Phase 1: 2개 (즉시 사용 가능, RSS)
- Phase 2: 8개 (핵심 확장, HTML)
- Phase 3: 3개 (고급 기능, JS/API)

**대륙별 균형:**
- OLD_WORLD: 7개 (54%)
- NEW_WORLD: 4개 (31%)
- ASIA: 2개 (15%)

**Purpose별 커버리지:**
- P1_daily_briefing: 6개 ✅
- P2_market_analysis: 6개 ✅
- P3_investment: 2개 ✅
- P4_trend_discovery: 7개 ✅
- P5_education: 8개 (Phase 3 연기)

**이 로드맵으로 신뢰도 높고 접근 가능하며 사용자 가치가 큰 소스부터 체계적으로 구축할 수 있습니다.**
