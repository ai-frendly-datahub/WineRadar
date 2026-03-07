# 데이터 소스 (Data Sources)

## 개요
WineRadar는 전 세계 와인 시장의 트렌드, 전문가 리뷰, 시장 통계 및 교육 자료를 수집하기 위해 다각화된 데이터 수집 전략을 사용합니다. 주요 수집 방식은 안정적인 RSS 피드와 유연한 HTML 스크래핑이며, 향후 REST API 연동을 계획하고 있습니다.

## 데이터 소스 목록
현재 WineRadar에서 활성화된 14개의 주요 데이터 소스 목록입니다.

| ID | 이름 | 국가 | 수집 방식 | 콘텐츠 유형 | 신뢰도 등급 |
|----|------|------|-----------|-------------|------------|
| media_wine21_kr | Wine21 | KR | HTML | news_review | T3_professional |
| media_winewhat_jp | WINE WHAT!? | JP | RSS | news_review | T3_professional |
| media_decanter_global | Decanter | GB | RSS | news_review | T2_expert |
| media_drinksbusiness_uk | The Drinks Business | GB | RSS | news_review | T3_professional |
| media_larvf_fr | La Revue du vin de France | FR | HTML | news_review | T2_expert |
| media_terredevins_fr | Terre de Vins | FR | RSS | news_review | T3_professional |
| media_gambero_it | Gambero Rosso | IT | RSS | news_review | T2_expert |
| media_wineenthusiast_us | Wine Enthusiast | US | RSS | news_review | T2_expert |
| media_vinography_us | Vinography | US | RSS | news_review | T3_professional |
| media_enolife_ar | Enolife | AR | RSS | news_review | T3_professional |
| media_winemag_za | Wine Magazine South Africa | ZA | RSS | news_review | T3_professional |
| media_acevinos_es | ACE Vinos | ES | RSS | news_review | T3_professional |
| media_vinepair_us | VinePair | US | RSS | news_review | T3_professional |
| media_punch_us | Punch | US | RSS | news_review | T3_professional |

## 소스별 상세 정보

### 1. 프리미엄 전문가 미디어 (T2_expert)
국제적인 권위를 인정받는 전문가 그룹이 운영하는 소스로, 와인 평가 및 심층 분석을 제공합니다.
- **Decanter (GB)**: `https://www.decanter.com/feed/` (RSS, 실시간)
- **Gambero Rosso (IT)**: `https://www.gamberorosso.it/feed/` (RSS, 실시간)
- **La Revue du vin de France (FR)**: `https://www.larvf.com/actualites` (HTML 스크래핑)
- **Wine Enthusiast (US)**: `https://www.wineenthusiast.com/feed/` (RSS, 일간)

### 2. 업계 전문 미디어 (T3_professional)
특정 지역이나 시장 트렌드에 특화된 전문 매체입니다.
- **Wine21 (KR)**: `https://www.wine21.com/11_news/news_list.html` (HTML, 한국 시장 필수)
- **The Drinks Business (UK)**: `https://www.thedrinksbusiness.com/feed/` (RSS, 글로벌 주류 무역)
- **WINE WHAT!? (JP)**: `https://wine-what.jp/feed/` (RSS, 일본 시장)
- **Terre de Vins (FR)**: `https://www.terredevins.com/feed` (RSS, 프랑스 라이프스타일)

## 신뢰도 평가
모든 데이터 소스는 [SOURCE_RELIABILITY_ASSESSMENT.md](SOURCE_RELIABILITY_ASSESSMENT.md)에 정의된 5개 차원(기관 신뢰도, 검증 가능성, 업데이트 일관성, 콘텐츠 품질, 접근 가능성)에 따라 평가됩니다. 

- **A+ 등급**: Decanter, Gambero Rosso 등 (즉시 사용 권장)
- **A 등급**: Wine21, Wine Review 등 (우선 사용 권장)

## 수집 제한사항 및 준수사항
- **robots.txt 준수**: 모든 HTML 수집기는 대상 사이트의 robots.txt 설정을 확인하고 준수합니다.
- **Rate Limiting**: 서버 부하를 방지하기 위해 요청 간격을 조절하며, `tenacity`를 이용한 재시도 로직을 적용합니다.
- **페이월(Paywall)**: Wine Spectator와 같이 구독이 필요한 프리미엄 콘텐츠는 현재 수집 대상에서 제외하거나 공개된 요약 정보만 활용합니다.
- **데이터 무결성**: 수집된 데이터는 `quality_checks/data_quality.py`를 통해 무결성 검증을 거칩니다.
