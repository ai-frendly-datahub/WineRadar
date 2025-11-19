# WineRadar 데이터 소스 현황 및 관리

## 문서 목적
이 문서는 WineRadar가 사용하는 와인 뉴스 데이터 소스의 현황, 테스트 결과, 그리고 각 소스의 특징과 한계를 상세히 기록합니다.

**최종 업데이트**: 2025-11-19
**활성 소스 수**: 13개 (RSS: 9개, HTML: 4개)
**테스트 완료**: 26개 소스

---

## 목차
1. [활성화된 소스 (Enabled)](#활성화된-소스)
2. [비활성화된 소스 및 사유](#비활성화된-소스)
3. [소스 추가 기준](#소스-추가-기준)
4. [테스트 방법론](#테스트-방법론)
5. [문제 해결 가이드](#문제-해결-가이드)

---

## 활성화된 소스

### 1. RSS 피드 소스 (C1_rss) - 9개

#### 🇬🇧 영국

##### Decanter
- **URL**: https://www.decanter.com/feed/
- **상태**: ✅ 정상 작동
- **신뢰도**: T2_expert (전문가 매체)
- **가중치**: 3.0
- **언어**: 영어
- **특징**: 국제적 권위, 안정적인 RSS 피드
- **최근 수집**: 정상
- **비고**: 와인 산업 표준 미디어

##### The Drinks Business
- **URL**: https://www.thedrinksbusiness.com/feed/
- **상태**: ✅ 정상 작동
- **신뢰도**: T3_professional (전문 매체)
- **가중치**: 2.6
- **언어**: 영어
- **특징**: 글로벌 음료 산업 트레이드 미디어
- **최근 수집**: 정상
- **비고**: 시장 트렌드 및 비즈니스 뉴스 강점

#### 🇫🇷 프랑스

##### Terre de Vins
- **URL**: https://www.terredevins.com/feed
- **상태**: ✅ 정상 작동
- **신뢰도**: T3_professional
- **가중치**: 2.6
- **언어**: 프랑스어
- **특징**: 프랑스 와인 라이프스타일 및 뉴스
- **최근 수집**: 정상
- **비고**: 구대륙 관점 제공

#### 🇮🇹 이탈리아

##### Gambero Rosso
- **URL**: https://www.gamberorosso.it/feed/
- **상태**: ✅ 정상 작동 (현재 주력 소스)
- **신뢰도**: T2_expert
- **가중치**: 3.0
- **언어**: 이탈리아어
- **특징**: 이탈리아 와인 권위, 매우 활발한 업데이트
- **최근 수집**: 전체의 84.2% 차지 (불균형)
- **비고**: 소스 다변화 필요성의 주요 이유

##### Vinogusto
- **URL**: https://www.vinogusto.com/feed/
- **상태**: ⚠️ 작동 (인코딩 이슈 있음)
- **신뢰도**: T3_professional
- **가중치**: 2.5
- **언어**: 이탈리아어
- **특징**: 이탈리아 와인 전자상거래 플랫폼
- **최근 테스트**: 10개 항목 수집, 특수문자 인코딩 주의 필요
- **비고**: cp949 인코딩 이슈 발생 가능

#### 🇺🇸 미국

##### Wine Enthusiast
- **URL**: https://www.wineenthusiast.com/feed/
- **상태**: ✅ 정상 작동
- **신뢰도**: T2_expert
- **가중치**: 2.9
- **언어**: 영어
- **특징**: 미국 기반 전문가 매체, 소비자 트렌드 및 평가
- **최근 수집**: 정상
- **비고**: 신대륙 관점 제공

##### Vinography
- **URL**: https://www.vinography.com/feed
- **상태**: ✅ 정상 작동
- **신뢰도**: T3_professional
- **가중치**: 2.4
- **언어**: 영어
- **특징**: 독립 와인 분석 블로그, 심층 커버리지
- **최근 수집**: 정상
- **비고**: 장문 분석 기사 강점

##### Wine & Spirits Magazine
- **URL**: https://www.winemag.com/feed/
- **상태**: ✅ 정상 작동
- **신뢰도**: T2_expert
- **가중치**: 2.8
- **언어**: 영어
- **특징**: 미국 와인 매거진, 광범위한 커버리지
- **최근 테스트**: 10개 항목 수집 성공
- **비고**: 레시피 및 페어링 콘텐츠 풍부

#### 🇿🇦 남아프리카공화국

##### Wine Magazine South Africa
- **URL**: https://www.winemag.co.za/feed/
- **상태**: ⚠️ 작동 (파싱 경고)
- **신뢰도**: T3_professional
- **가중치**: 2.5
- **언어**: 영어
- **특징**: 남아공 와인 라이프스타일
- **최근 테스트**: unbound prefix 파싱 경고, 10개 항목 수집
- **비고**: 신대륙 다변화에 기여

---

### 2. HTML 스크래핑 소스 (C2_html_simple) - 4개

#### 🇰🇷 한국

##### Wine21
- **URL**: https://www.wine21.com/11_news/reporter_news_list.html
- **상태**: ⚠️ 작동 불안정
- **신뢰도**: T3_professional
- **가중치**: 2.8
- **언어**: 한국어
- **특징**: 한국 전문 와인 미디어
- **최근 수집**: 추출 실패 (article_selector 문제)
- **비고**: 셀렉터 재조정 필요

##### Wine Review
- **URL**: https://winereview.co.kr/news
- **상태**: ❌ 404 에러
- **신뢰도**: T3_professional
- **가중치**: 2.8
- **언어**: 한국어
- **특징**: 한국 와인 전문 출판
- **최근 테스트**: URL 변경 추정
- **비고**: URL 업데이트 필요

#### 🇫🇷 프랑스

##### La Revue du vin de France
- **URL**: https://www.larvf.com/actualites
- **상태**: ❌ 404 에러
- **신뢰도**: T2_expert
- **가중치**: 3.0
- **언어**: 프랑스어
- **특징**: 프랑스 와인 권위
- **최근 테스트**: 사이트 구조 변경 추정
- **비고**: URL 업데이트 필요

#### 🇨🇳 중국

##### Wines of China
- **URL**: https://www.winesofchina.com/news
- **상태**: 🔄 테스트 필요
- **신뢰도**: T3_professional
- **가중치**: 2.4
- **언어**: 영어
- **특징**: 중국 와인 시장 뉴스
- **최근 테스트**: 미실시
- **비고**: 아시아 시장 다변화

#### 🇯🇵 일본

##### Japan Wine
- **URL**: https://japan-wine.jp/news/
- **상태**: 🔄 테스트 필요
- **신뢰도**: T3_professional
- **가중치**: 2.3
- **언어**: 일본어
- **특징**: 일본 와인 산업 뉴스
- **최근 테스트**: 미실시
- **비고**: 아시아 다변화

---

## 비활성화된 소스

### RSS 피드 문제 (404/403)

#### Jancis Robinson (media_jancisrobinson_uk)
- **이유**: 404 Not Found
- **URL**: https://www.jancisrobinson.com/articles/feed
- **테스트 날짜**: 2025-11-19
- **해결 방안**: RSS 피드 URL 재확인, 구독 필요 여부 확인
- **우선순위**: 높음 (Master of Wine 권위)

#### Wine-Searcher (media_winesearcher_global)
- **이유**: 403 Forbidden
- **URL**: https://www.wine-searcher.com/rss.lml
- **테스트 날짜**: 2025-11-19
- **해결 방안**: User-Agent 조정, API 키 필요 여부 확인
- **우선순위**: 중간 (가격 데이터 유용)

#### Vinetur (media_vinetur_es)
- **이유**: 404 Not Found
- **URL**: https://www.vinetur.com/feed/
- **테스트 날짜**: 2025-11-19
- **해결 방안**: 올바른 RSS URL 찾기
- **우선순위**: 중간 (스페인 시장 커버리지)

#### The World's 50 Best (media_worlds50best_uk)
- **이유**: 404 Not Found
- **URL**: https://www.theworlds50best.com/stories/feed
- **테스트 날짜**: 2025-11-19
- **해결 방안**: RSS URL 재확인
- **우선순위**: 낮음 (글로벌 어워드 중심)

#### Austin Wine Journal (media_austinwine_us)
- **이유**: DNS 해석 실패
- **URL**: https://www.austinwinejournal.com/feed/
- **테스트 날짜**: 2025-11-19
- **해결 방안**: 도메인 상태 확인, 대체 URL 찾기
- **우선순위**: 낮음 (지역 매체)

#### Meininger's (media_meininger_de)
- **이유**: 403 Forbidden
- **URL**: https://www.meininger.de/en/rss.xml
- **테스트 날짜**: 2025-11-19
- **해결 방안**: User-Agent 조정, 구독 필요 여부 확인
- **우선순위**: 높음 (독일 트레이드 미디어)

### HTML 스크래핑 문제

#### 한국 소스 (Wine21, Wine Review)
- **이유**: article_selector 미설정 또는 URL 변경
- **해결 방안**:
  1. 각 사이트의 HTML 구조 재분석
  2. 올바른 CSS 셀렉터 설정
  3. URL 변경 여부 확인
- **우선순위**: 높음 (한국 시장 커버리지 중요)

#### 공식 기관 소스 (다수)
- **소스**: IFV (프랑스), ICEX (스페인), Wines of Germany, Wine Institute (미국) 등
- **이유**: 403/404 에러
- **공통 특징**:
  - 대부분 정부/협회 사이트
  - 통계 및 교육 콘텐츠 중심
  - 업데이트 빈도 낮음
- **해결 방안**:
  1. User-Agent 설정
  2. 봇 차단 우회 전략
  3. 공식 API 존재 여부 확인
- **우선순위**: 중간 (시장 분석용)

---

## 소스 추가 기준

### 1. 기술적 요구사항
- ✅ RSS 피드 제공 (우선순위 높음)
- ✅ 안정적인 HTML 구조 (스크래핑용)
- ✅ robots.txt 허용
- ✅ 적절한 업데이트 빈도 (주 1회 이상)

### 2. 콘텐츠 품질
- ✅ 신뢰할 수 있는 발행처
- ✅ 와인 산업 관련성
- ✅ 독창적 콘텐츠 (단순 재배포 아님)
- ✅ 명확한 출처 및 날짜

### 3. 다양성 목표
- **지역 균형**: 구대륙 (40-50%), 신대륙 (30-40%), 아시아 (10-20%)
- **언어 다양성**: 영어 (50%), 프랑스어/이탈리아어 (30%), 기타 (20%)
- **콘텐츠 타입**: 뉴스 (60%), 시장 분석 (20%), 교육 (20%)
- **신뢰도**: T1 (10%), T2 (40%), T3 (50%)

### 4. 현재 불균형 해소 목표
| 지역 | 현재 | 목표 |
|------|------|------|
| 구대륙 (유럽) | 92.1% | 50% |
| 아시아 | 5.0% | 15% |
| 신대륙 | 2.9% | 35% |

**주요 문제**: Gambero Rosso 84.2% 독점 → 20% 이하로 감소 필요

---

## 테스트 방법론

### 자동화된 테스트 스크립트
```bash
python test_new_sources.py
```

### 수동 테스트 절차
1. **RSS 피드 확인**
   ```bash
   curl -I https://example.com/feed/
   ```

2. **feedparser 검증**
   ```python
   import feedparser
   feed = feedparser.parse('https://example.com/feed/')
   print(f"Entries: {len(feed.entries)}")
   ```

3. **HTML 스크래핑 테스트**
   ```python
   from collectors.html_collector import HTMLCollector
   collector = HTMLCollector(source_meta)
   items = list(collector.collect())
   ```

### 테스트 체크리스트
- [ ] HTTP 응답 코드 200
- [ ] RSS 파싱 에러 없음
- [ ] 최소 3개 이상 항목 추출
- [ ] title, url, published_at 필수 필드 존재
- [ ] 인코딩 문제 없음
- [ ] 지속적 접근 가능 (24시간 테스트)

---

## 문제 해결 가이드

### 403 Forbidden 에러
**증상**: 서버가 요청을 거부
**원인**:
- 봇 차단
- User-Agent 필터링
- Rate limiting
- IP 블랙리스트

**해결 방안**:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml',
    'Accept-Language': 'en-US,en;q=0.9',
}
response = requests.get(url, headers=headers, timeout=10)
```

### 404 Not Found 에러
**증상**: URL이 존재하지 않음
**원인**:
- URL 변경
- 사이트 리뉴얼
- RSS 피드 중단

**해결 방안**:
1. 사이트 메인 페이지에서 RSS 링크 찾기
2. `/feed`, `/rss`, `/feed.xml`, `/rss.xml` 시도
3. 사이트 sitemap 확인
4. 고객 지원 문의

### 인코딩 에러 (cp949)
**증상**: UnicodeEncodeError
**원인**: Windows 콘솔 cp949 인코딩이 특수문자 미지원

**해결 방안**:
```python
# 1. 콘솔 출력 시 에러 무시
print(text, errors='ignore')

# 2. UTF-8로 변환
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 3. 파일 저장 시 UTF-8 지정
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(text)
```

### article_selector 문제
**증상**: "No articles extracted"
**원인**: CSS 셀렉터가 HTML 구조와 불일치

**해결 방안**:
1. **브라우저 개발자 도구로 확인**
   - F12 → Elements
   - 기사 링크 우클릭 → Copy selector

2. **일반적인 셀렉터 패턴**
   ```yaml
   article_selector: article.post
   link_selector: h2.entry-title a
   summary_selector: div.excerpt
   date_selector: time
   ```

3. **테스트 방법**
   ```python
   from bs4 import BeautifulSoup
   import requests

   html = requests.get(url).text
   soup = BeautifulSoup(html, 'html.parser')
   articles = soup.select('article.post')
   print(f"Found {len(articles)} articles")
   ```

---

## 다음 단계 로드맵

### 단기 (1주)
- [ ] Wine21 셀렉터 수정
- [ ] Wine Review URL 업데이트
- [ ] Jancis Robinson RSS URL 재확인
- [ ] 중국/일본 소스 테스트

### 중기 (1개월)
- [ ] Meininger's 403 에러 해결
- [ ] 공식 기관 소스 재시도 (User-Agent 조정)
- [ ] 호주/뉴질랜드 소스 추가
- [ ] 남미 소스 (칠레/아르헨티나) 추가

### 장기 (3개월)
- [ ] Wine Spectator API 협상
- [ ] 자체 RSS 모니터링 시스템 구축
- [ ] 머신러닝 기반 소스 품질 평가
- [ ] 사용자 피드백 기반 소스 가중치 조정

---

## 변경 이력

### 2025-11-19
- 초기 문서 작성
- 9개 RSS 소스 추가 및 테스트 완료
- Wine & Spirits Magazine 추가 (✅ 작동 확인)
- Vinogusto 추가 (⚠️ 인코딩 이슈)
- Wine Magazine SA 추가 (⚠️ 파싱 경고)
- 6개 소스 404/403 에러로 비활성화
- Gambero Rosso 독점 문제 확인 (84.2%)

---

## 관련 문서
- [SOURCE_STRATEGY.md](SOURCE_STRATEGY.md) - 소스 선정 전략
- [DEPLOYMENT.md](DEPLOYMENT.md) - 배포 및 스케줄링
- [API_SPEC.md](API_SPEC.md) - 수집기 인터페이스

---

**문서 관리자**: WineRadar Team
**연락처**: Issues - https://github.com/<username>/WineRadar/issues
