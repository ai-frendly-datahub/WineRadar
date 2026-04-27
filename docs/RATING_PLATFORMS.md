# 글로벌 와인 평점/리뷰 플랫폼 통합 전략

## 개요

Vivino, Wine Spectator, Robert Parker 등 글로벌 평점 플랫폼은 WineRadar의 **트렌드 감지 정확도**와 **인사이트 깊이**를 획기적으로 향상시킬 수 있는 데이터 소스입니다.

**왜 중요한가:**
1. **시장 영향력**: Parker 점수 90점 이상 → 가격 20-30% 상승 (실증)
2. **소비자 행동**: Vivino 평점 4.0+ → 구매 전환율 2배 이상
3. **트렌드 선행지표**: Top 100 리스트 → 6개월 후 수입 증가 패턴

## 플랫폼별 상세 분석

### 1. Vivino (소비자 평점 플랫폼)

#### 기본 정보
- **URL**: https://www.vivino.com
- **유형**: UGC (User Generated Content) 평점/리뷰
- **데이터**: 유저 평점 (5점 만점), 가격, 구매처, 페어링 제안
- **전 세계 유저**: 6천만+ (2024 기준)

#### 수집 가능 데이터
```yaml
vivino_data_points:
  - wine_rating: 평점 (1-5점, 소수점 1자리)
  - num_ratings: 평가 개수 (신뢰도 지표)
  - price_range: 가격대 (지역별 차이)
  - popular_regions: 인기 지역/국가
  - trending_wines: 트렌딩 와인 목록
  - user_reviews: 사용자 리뷰 텍스트 (감정 분석 가능)
  - food_pairing: 음식 페어링 추천 (크라우드소싱)
```

#### 기술적 접근
```yaml
collection_method: "hybrid"
approaches:
  primary: "html_scraping"
    - 검색 결과 페이지 파싱
    - 와인 상세 페이지 크롤링
    - JavaScript 렌더링 필요 (Selenium/Playwright)

  fallback: "api_reverse_engineering"
    - 모바일 앱 API 엔드포인트 분석 (비공식)
    - rate_limit: 매우 엄격 (IP 차단 위험)
    - 추천하지 않음 (TOS 위반 가능성)

  recommended: "manual_snapshots"
    - 주간/월간 Top 100 수동 스냅샷
    - 주요 품종/지역 랭킹 정기 수집
    - MCP 응답용 캐싱 데이터로 활용
```

#### 활용 시나리오
```python
# Q1 답변: 소비자 감정 vs 뉴스 트렌드 비교
vivino_sentiment = analyze_vivino_reviews(wine="Bordeaux 2020")
# → {"positive": 0.65, "neutral": 0.25, "negative": 0.10}

news_trend = get_news_trend(topic="Bordeaux", time_window=30)
# → {"mentions": 45, "tone": "cautious", "keywords": ["frost", "vintage"]}

# 비교: Vivino는 긍정적이지만 뉴스는 신중
# → 인사이트: 소비자는 아직 서리 피해 소식 모름, 조기 경보 필요
```

### 2. Wine Spectator (전문가 리뷰)

#### 기본 정보
- **URL**: https://www.winespectator.com
- **유형**: 전문가 평론 (100점 척도)
- **데이터**: 시음 점수, Top 100, Vintage Chart, 뉴스
- **구독 모델**: Freemium (일부 무료, 대부분 유료)

#### 수집 가능 데이터
```yaml
wine_spectator_data:
  free_access:
    - top_100_list: 연간 Top 100 와인 (공개)
    - news_articles: 뉴스/칼럼 일부
    - vintage_charts: 주요 산지 빈티지 평가 (요약)

  premium_required:
    - detailed_scores: 상세 점수 (100점)
    - tasting_notes: 시음 노트
    - cellar_recommendations: 숙성 추천
```

#### 기술적 접근
```yaml
collection_method: "selective_scraping"
strategies:
  - free_content_only: true  # TOS 준수
  - targets:
      - "/top100": 연간 리스트
      - "/articles": 무료 뉴스
      - "/blogs": 칼럼니스트 블로그
  - avoid:
      - "/ratings-reviews/*": 유료 구독 전용
```

#### 활용 시나리오
```python
# Top 100 이력 추적
top100_history = track_top100(years=[2020, 2021, 2022, 2023, 2024])
# → {"Cabernet Sauvignon": [15, 18, 22, 25, 28]}  # 출현 빈도 증가
# → 인사이트: 카베르네 소비뇽 인기 지속 상승
```

### 3. Robert Parker / Wine Advocate (파커 점수)

#### 기본 정보
- **URL**: https://www.robertparker.com
- **유형**: 전문가 평점 (100점 척도)
- **영향력**: **업계 표준** (90+ = 프리미엄, 95+ = 수집가급)
- **구독 모델**: 유료 (연간 $99+)

#### 데이터 가치
```yaml
parker_score_impact:
  score_90_plus:
    - price_increase: +20-30%
    - retail_demand: +150%
    - collector_interest: High

  score_95_plus:
    - price_increase: +50-100%
    - allocation_scarcity: 발생 (품귀)
    - investment_grade: 와인 투자 대상

  score_100:
    - legendary_status: 전설급 와인
    - price: Sky-high (수십만원~)
```

#### 기술적 접근
```yaml
collection_method: "limited_public_only"
strategies:
  - free_content:
      - vintage_reports: 빈티지 요약 (일부)
      - winery_profiles: 와이너리 소개
      - news: 업계 뉴스

  - ethical_approach:
      - 유료 콘텐츠 크롤링 금지
      - 공개 요약/샘플만 수집
      - 출처 명시 필수
```

#### 활용 시나리오
```python
# Q2 답변: 고득점 트렌드를 MCP 응답에 반영
high_scores = get_parker_scores(threshold=95, vintage=2020)
# → [{"wine": "Château Margaux", "score": 98}, ...]

# MCP 응답 예시
user_query = "2020년 보르도 투자 추천?"
mcp_response = {
    "recommendation": "Château Margaux 2020 (Parker 98점)",
    "rationale": "파커 95+ 점수로 장기 가격 상승 가능성 높음",
    "risk": "높은 초기 비용, 유동성 제한"
}
```

### 4. James Suckling (아시아 시장 영향력)

#### 기본 정보
- **URL**: https://www.jamessuckling.com
- **특징**: 최근 아시아 시장 집중 (홍콩, 중국, 한국)
- **형식**: 100점 척도 + 영상 리뷰

#### 한국 시장 관련성
```yaml
korea_relevance:
  - asian_focus: 아시아 와인 페어 주최/참여
  - korean_importers: 한국 수입사와 협업 多
  - premium_segment: 고가 와인 마케팅 활용
```

### 5. Wine Enthusiast

#### 기본 정보
- **URL**: https://www.winemag.com
- **특징**: 교육 + 평론 혼합
- **접근성**: RSS 일부 지원, HTML 크롤링 가능

## 통합 sources.yaml 설계

### 평점 플랫폼 전용 섹션

```yaml
# config/sources.yaml 추가
sources:
  # === 평점/리뷰 플랫폼 ===
  - name: "Vivino"
    id: "rating_vivino_global"
    type: "rating_platform"      # 새 타입
    country: "GLOBAL"
    continent: "GLOBAL"
    region: "Global/Consumer"
    tier: "community"             # UGC 기반
    content_type: "consumer_rating"
    language: "en"
    enabled: false                # Phase 2+
    weight: 2.5
    supports_rss: false
    requires_login: false
    notes: "User-generated ratings, trending wines, price data"
    config:
      list_url: "https://www.vivino.com/explore"
      collection_method: "html"
      scraping_difficulty: "high"  # JS 렌더링 필요
      data_points: ["rating", "num_ratings", "price", "trending"]

  - name: "Wine Spectator"
    id: "rating_winespectator_us"
    type: "rating_platform"
    country: "US"
    continent: "GLOBAL"
    region: "Global/Expert"
    tier: "premium"
    content_type: "expert_rating"
    language: "en"
    enabled: false                # Phase 2+
    weight: 3.0
    supports_rss: true            # 일부 섹션
    requires_login: true          # 대부분 콘텐츠
    notes: "Top 100, vintage charts, expert scores (100-point scale)"
    config:
      list_url: "https://www.winespectator.com/top100"
      collection_method: "html"
      ethical_constraint: "free_content_only"  # 유료 콘텐츠 제외

  - name: "Robert Parker Wine Advocate"
    id: "rating_parker_global"
    type: "rating_platform"
    country: "GLOBAL"
    continent: "GLOBAL"
    region: "Global/Expert"
    tier: "premium"
    content_type: "expert_rating"
    language: "en"
    enabled: false
    weight: 3.0
    supports_rss: false
    requires_login: true
    notes: "Parker scores (industry standard), vintage reports"
    config:
      list_url: "https://www.robertparker.com/resources/vintage-chart"
      collection_method: "html"
      ethical_constraint: "free_content_only"

  - name: "James Suckling"
    id: "rating_suckling_asia"
    type: "rating_platform"
    country: "GLOBAL"
    continent: "GLOBAL"
    region: "Global/Expert/Asia"
    tier: "premium"
    content_type: "expert_rating"
    language: "en"
    enabled: false
    weight: 2.8
    supports_rss: false
    requires_login: true
    notes: "Asian market focus, video reviews, 100-point scale"
    config:
      list_url: "https://www.jamessuckling.com"
      collection_method: "html"
```

## Q1-Q3 답변: 실전 활용 전략

### Q1: Vivino 리뷰 감정 분석 vs 뉴스 트렌드 비교

**시나리오: 소비자 반응 vs 업계 뉴스 갭 감지**

```python
# analyzers/sentiment_analyzer.py
def compare_vivino_vs_news(wine_or_region: str) -> dict:
    """
    Vivino 유저 감정과 뉴스 톤을 비교하여 정보 비대칭 감지

    Returns:
        {
            "vivino_sentiment": {"positive": 0.7, "neutral": 0.2, "negative": 0.1},
            "news_sentiment": {"positive": 0.3, "neutral": 0.4, "negative": 0.3},
            "gap_analysis": "소비자는 긍정적이나 뉴스는 부정적 → 조기 경보 필요",
            "recommendation": "수입사/유통사는 소비자 교육 준비"
        }
    """
    vivino_reviews = fetch_vivino_reviews(wine_or_region)
    news_articles = get_news(topic=wine_or_region, days=30)

    vivino_sentiment = sentiment_analysis(vivino_reviews)  # NLP
    news_sentiment = sentiment_analysis(news_articles)

    gap = calculate_sentiment_gap(vivino_sentiment, news_sentiment)

    return {
        "vivino_sentiment": vivino_sentiment,
        "news_sentiment": news_sentiment,
        "gap_analysis": interpret_gap(gap),
        "recommendation": generate_recommendation(gap)
    }
```

**View 설계: Sentiment Gap Report**
```python
{
    "name": "Sentiment Gap Report",
    "description": "소비자 vs 전문가/뉴스 감정 차이",
    "sections": [
        {
            "title": "소비자 과열 경보",
            "filter": "vivino_positive > 0.7 AND news_negative > 0.3",
            "interpretation": "소비자는 긍정적이나 업계는 신중 → 버블 위험"
        },
        {
            "title": "숨은 기회",
            "filter": "vivino_neutral > 0.5 AND expert_score > 90",
            "interpretation": "소비자 인지 낮지만 전문가 평가 높음 → 발굴 기회"
        }
    ]
}
```

### Q2: 전문가 점수 기반 고득점/저득점 트렌드 MCP 반영

**시나리오: MCP가 Parker/Spectator 점수로 투자 가치 판단**

```python
# mcp_server/wine_investment_tool.py
def evaluate_investment_potential(wine: str, vintage: int) -> dict:
    """
    전문가 점수를 활용한 와인 투자 가치 평가

    Returns:
        {
            "wine": "Château Margaux 2020",
            "scores": {
                "parker": 98,
                "spectator": 96,
                "suckling": 99,
                "average": 97.7
            },
            "investment_grade": "Exceptional (95+)",
            "price_appreciation_forecast": "+50-80% in 5 years",
            "liquidity": "High (collector demand)",
            "risks": ["Storage costs", "Market volatility"]
        }
    """
    scores = {
        "parker": get_parker_score(wine, vintage),
        "spectator": get_spectator_score(wine, vintage),
        "suckling": get_suckling_score(wine, vintage)
    }

    avg_score = sum(scores.values()) / len(scores)

    if avg_score >= 95:
        grade = "Exceptional"
        forecast = "+50-80% in 5 years"
    elif avg_score >= 90:
        grade = "Excellent"
        forecast = "+20-40% in 5 years"
    else:
        grade = "Good"
        forecast = "+5-15% in 5 years"

    return {
        "wine": f"{wine} {vintage}",
        "scores": scores,
        "investment_grade": grade,
        "price_appreciation_forecast": forecast
    }
```

**MCP 대화 예시:**
```
User: "2020년 보르도 와인 중 투자 가치 높은 것 추천해줘"

MCP: "2020년 보르도에서 Parker 95점 이상을 받은 와인 3개를 찾았습니다:

1. Château Margaux 2020 (Parker 98, Spectator 96)
   - 투자 등급: Exceptional
   - 5년 예상 수익: +50-80%
   - 현재 가격: $800-1,000/bottle
   - 리스크: 높은 초기 비용, 보관 필수

2. Château Lafite Rothschild 2020 (Parker 97)
   - 투자 등급: Exceptional
   - 중국 시장 수요 높음 → 유동성 우수

3. Château Haut-Brion 2020 (Parker 96)
   - 상대적 저평가 → 가격 상승 여력"
```

### Q3: 품종·국가별 스코어 히트맵

**시나리오: 전문가 점수 기반 트렌드 시각화**

```python
# reporters/heatmap_generator.py
def generate_score_heatmap(
    years: list[int] = [2018, 2019, 2020, 2021, 2022],
    score_source: str = "parker"
) -> pd.DataFrame:
    """
    품종·국가별 평균 점수 히트맵 데이터 생성

    Returns:
        DataFrame:
                    FR    IT    US    AU    CL
        Cab Sauv    92    88    90    89    85
        Pinot Noir  94    87    91    88    82
        Chardonnay  90    85    92    91    84
    """
    data = {}
    varieties = ["Cabernet Sauvignon", "Pinot Noir", "Chardonnay", ...]
    countries = ["FR", "IT", "US", "AU", "CL", ...]

    for variety in varieties:
        data[variety] = {}
        for country in countries:
            avg_score = get_avg_score(
                variety=variety,
                country=country,
                years=years,
                source=score_source
            )
            data[variety][country] = avg_score

    return pd.DataFrame(data).T
```

**시각화 출력 (HTML 리포트):**
```
┌─────────────────────────────────────────────────────┐
│ Parker Score Heatmap (2018-2022 Average)            │
├─────────────────────────────────────────────────────┤
│                  FR   IT   US   AU   CL   AR   ES   │
│ Cabernet Sauv.   🟥92 🟨88 🟨90 🟨89 🟧85 🟧84 🟨87 │
│ Pinot Noir       🟥94 🟨87 🟨91 🟨88 🟧82 🟧80 🟨86 │
│ Chardonnay       🟨90 🟧85 🟥92 🟨91 🟧84 🟧83 🟧85 │
│ Syrah/Shiraz     🟨89 🟧85 🟨88 🟥93 🟧86 🟧87 🟨88 │
│ Merlot           🟨91 🟨88 🟨87 🟧85 🟧87 🟧86 🟨89 │
└─────────────────────────────────────────────────────┘
🟥 95+ (Exceptional) | 🟨 90-94 (Excellent) | 🟧 85-89 (Very Good)

Insights:
- 프랑스 피노누아 최고 (94점) → 부르고뉴 강세
- 호주 시라즈 돌풍 (93점) → Barossa Valley 주목
- 미국 샤도네이 약진 (92점) → 캘리포니아 스타일 진화
```

## 구현 우선순위

### Phase 1 (현재): 문서화 및 설계
- ✅ 평점 플랫폼 분석 완료
- ✅ sources.yaml 스키마 확장
- ✅ 윤리적 수집 가이드라인 정립

### Phase 2 (3-4주 후): 공개 데이터만 수집
- Wine Spectator Top 100 수집 (연간)
- Parker Vintage Chart 스냅샷 (분기)
- Vivino Top Trending 목록 (주간)

### Phase 3 (확장): 통합 분석
- 감정 분석 파이프라인 (Vivino 리뷰)
- 점수 기반 투자 등급 계산
- 히트맵 생성 및 HTML 리포트 통합

## 윤리적 고려사항

### DO's ✅
1. **공개 콘텐츠만 수집**: 무료/공개 섹션에서만 데이터 추출
2. **Rate Limiting 준수**: robots.txt 확인, 요청 간격 최소 5초
3. **출처 명시**: 모든 리포트에 데이터 출처 명시
4. **변환 가치 추가**: 단순 복사 X, 분석/인사이트 제공 O

### DON'Ts ❌
1. **유료 콘텐츠 우회 금지**: 페이월 회피 시도 금지
2. **API 역공학 금지**: 비공식 API 사용 금지 (Vivino 등)
3. **대량 크롤링 금지**: 서버 부하 초래 금지
4. **상업적 재판매 금지**: 점수 DB 판매 금지

### TOS 준수 전략
```yaml
ethical_framework:
  - respect_paywall: true
  - cite_sources: always
  - add_value: analysis_only  # 원본 복사 X
  - rate_limit: 5_seconds_minimum
  - robots_txt: obey_strictly
```

## 결론

평점 플랫폼 통합으로:
1. **예측력 향상**: 소비자 반응 + 전문가 평가 → 시장 선행지표
2. **인사이트 깊이**: 단순 뉴스 수집 → 투자 가치 판단
3. **차별화**: 다른 와인 정보 서비스와 차별화 (MCP 통합)

**다음 단계:**
- sources.yaml에 평점 플랫폼 추가
- Wine Spectator Top 100 스크레이퍼 프로토타입
- 감정 분석 파이프라인 설계 (analyzers/sentiment.py)
