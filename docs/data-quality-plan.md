# Data Quality Plan

- 생성 시각: `2026-04-23T14:45:24.863320+00:00`
- 우선순위: `P1`
- 데이터 품질 점수: `76`
- 가장 약한 축: `운영 깊이`
- Governance: `medium`
- Primary Motion: `intelligence`

## 현재 이슈

- 가장 약한 품질 축은 운영 깊이(45)

## 필수 신호

- 경매 낙찰가와 통화·빈티지·생산자 정보
- 레스토랑 와인리스트와 가격 변동
- 수입사 portfolio와 유통 가능성 신호

## 품질 게이트

- 생산자·와인명·빈티지·appellation을 canonical wine key로 정규화
- 낙찰일·리스트 업데이트일·수집일을 별도 필드로 유지
- 비활성 고가치 source는 skip 사유와 재시도 정책을 남김

## 다음 구현 순서

- 비활성 고가치 source의 freshness/skip 사유를 우선 점검
- auction price와 restaurant wine list source를 운영 레이어로 추가
- importer portfolio sales 후보를 별도 capability/source로 분리 평가

## 운영 규칙

- 원문 URL, 수집일, 이벤트 발생일은 별도 필드로 유지한다.
- 공식 source와 커뮤니티/시장 source를 같은 신뢰 등급으로 병합하지 않는다.
- collector가 인증키나 네트워크 제한으로 skip되면 실패를 숨기지 말고 skip 사유를 기록한다.
- 이 문서는 `scripts/build_data_quality_review.py --write-repo-plans`로 재생성한다.
