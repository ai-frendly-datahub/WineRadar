# WineRadar 개발 로드맵

## 프로젝트 목표

와인 관련 웹 링크를 그래프 형태로 수집/분석하여, 관점별(와이너리/수입사/토픽) 트렌드를 탐색하는 자동화된 데일리 리포트 시스템 구축

## 전체 일정 개요

- **Phase 1**: 기본 인프라 구축 (2주)
- **Phase 2**: 데이터 수집 및 분석 (3주)
- **Phase 3**: 리포팅 시스템 (2주)
- **Phase 4**: 알림 및 최적화 (1주)
- **Total**: 약 8주 (MVP 완성)

---

## Phase 1: 기본 인프라 구축 (Week 1-2)

### 목표
실행 가능한 최소한의 데이터 저장 및 조회 시스템 구축

### 주요 작업

#### 1.1 개발 환경 설정
- [ ] Python 3.11+ 환경 구성
- [ ] 의존성 패키지 추가 및 정리
  - feedparser, python-dateutil, pydantic
- [ ] 코드 품질 도구 설정
  - mypy, black, ruff
  - pre-commit hooks 설정
- [ ] pytest 환경 구축
  - `tests/` 디렉토리 구조 생성
  - 기본 테스트 실행 환경 검증

**완료 조건**: `pytest`, `mypy`, `black` 실행 성공

#### 1.2 설정 관리 시스템
- [ ] config 로더 구현 (`config/loader.py`)
  - YAML 파일 파싱
  - Pydantic 모델 기반 검증
  - 환경변수 오버라이드 지원
- [ ] 설정 스키마 정의 (`config/schemas.py`)
- [ ] 단위 테스트 작성

**완료 조건**: `config.yaml`, `sources.yaml` 로드 및 검증 성공

#### 1.3 그래프 스토어 구현 (SQLite)
- [ ] 데이터베이스 스키마 설계
  - nodes 테이블 (url, winery, importer, topic, wine)
  - edges 테이블 (url ↔ entity 관계)
  - metadata 테이블 (시스템 정보)
- [ ] graph_store.py 함수 구현
  - `init_database()`: 스키마 초기화
  - `upsert_node()`: 노드 삽입/갱신
  - `upsert_edge()`: 엣지 삽입/갱신
  - `upsert_url_and_entities()`: 통합 저장
  - `prune_expired_urls()`: TTL 기반 정리
  - `get_nodes_by_type()`: 타입별 조회
- [ ] 인덱스 최적화
- [ ] 트랜잭션 처리
- [ ] 단위 테스트 작성

**완료 조건**: 노드/엣지 CRUD 및 pruning 테스트 통과

#### 1.4 로깅 시스템
- [ ] logging 모듈 설정 (`utils/logging_config.py`)
  - 콘솔 출력 (INFO 레벨)
  - 파일 로깅 (DEBUG 레벨, logs/ 디렉토리)
  - 로그 rotation 설정
- [ ] main.py에 로거 적용

**완료 조건**: 로그 파일 생성 및 레벨별 출력 확인

### Phase 1 마일스톤
- ✅ SQLite에 데이터 저장/조회 가능
- ✅ 설정 파일 로드 및 검증 가능
- ✅ 테스트 실행 환경 구축
- ✅ 기본 로깅 동작

---

## Phase 2: 데이터 수집 및 분석 (Week 3-5)

### 목표
실제 웹 소스에서 데이터를 수집하고 와인 관련 항목을 필터링/분석

### 주요 작업

#### 2.1 Collector 구현
- [ ] RSS Collector 기본 클래스 (`collectors/rss_collector.py`)
  - feedparser 활용
  - RawItem 변환 로직
  - 에러 핸들링 (개별 아이템 실패 허용)
- [ ] 소스별 Collector 구현
  - [ ] Wine21Collector (한국)
  - [ ] DecanterCollector (글로벌)
  - [ ] 기타 RSS 소스 2-3개 추가
- [ ] CollectorFactory 구현
  - sources.yaml 기반 인스턴스 생성
  - 소스별 가중치 적용
- [ ] 단위 테스트 및 통합 테스트

**완료 조건**: 실제 RSS 피드에서 RawItem 수집 성공

#### 2.2 키워드 필터링
- [ ] keyword_filter.py 구현
  - frequency_words.txt 파싱
  - 필수 키워드 (+) 검증
  - 제외 키워드 (!) 필터링
  - 일반 키워드 매칭
  - FilteredItem 생성
- [ ] 필터 규칙 최적화
  - 와인 관련 키워드 확장
  - 노이즈 제거 규칙 추가
- [ ] 테스트 케이스 작성
  - 긍정/부정 샘플 데이터

**완료 조건**: 필터링 정확도 90% 이상

#### 2.3 엔티티 추출
- [ ] entity_extractor.py 구현
  - 와이너리 추출 (룰 기반)
  - 수입사 추출 (사전 기반)
  - 토픽 추출 (키워드 패턴)
  - 와인명 추출 (선택적)
- [ ] 엔티티 사전 구축
  - `config/entities/wineries.yaml`
  - `config/entities/importers.yaml`
  - `config/entities/topics.yaml`
- [ ] 신뢰도 점수 부여
- [ ] 테스트 작성

**완료 조건**: 주요 엔티티(와이너리, 수입사) 80% 이상 추출

#### 2.4 스코어링 시스템
- [ ] scoring.py 구현
  - 소스 가중치 (sources.yaml의 weight)
  - 신선도 점수 (published_at 기반)
  - 엔티티 연결 점수 (인기 와이너리 가산점)
  - 종합 점수 계산
- [ ] 점수 튜닝
- [ ] 테스트 작성

**완료 조건**: ViewItem 정렬 시 합리적인 순서

#### 2.5 메인 파이프라인 통합
- [ ] main.py 구현
  1. 설정 로드
  2. Collector 실행
  3. 필터링
  4. 엔티티 추출
  5. 그래프 저장
  6. 통계 로깅
- [ ] 에러 복구 로직
  - Collector 실패 시 다음 소스 진행
  - 부분 실패 허용
- [ ] 진행 상황 로깅

**완료 조건**: `python main.py` 실행 시 데이터 수집 → 저장 완료

### Phase 2 마일스톤
- ✅ 실제 RSS 소스에서 데이터 수집
- ✅ 와인 관련 항목만 필터링
- ✅ 엔티티 추출 및 그래프 저장
- ✅ end-to-end 파이프라인 실행 가능

---

## Phase 3: 리포팅 시스템 (Week 6-7)

### 목표
그래프 데이터를 조회하고 HTML 데일리 리포트 생성

### 주요 작업

#### 3.1 그래프 쿼리 구현
- [ ] graph_queries.py 함수 구현
  - `get_view()`: 관점별 URL 조회
    - winery: 특정 와이너리 관련 링크
    - importer: 특정 수입사 관련 링크
    - topic: 특정 토픽 관련 링크
    - community: 커뮤니티 소스만
    - wine: 특정 와인 관련 링크
  - `get_top_entities()`: 기간별 인기 엔티티
  - `get_daily_stats()`: 일일 통계
- [ ] 시간 윈도우 처리 (최근 7일, 30일 등)
- [ ] 캐싱 전략 (선택적)
- [ ] 테스트 작성

**완료 조건**: 각 view 타입별 ViewItem 리스트 반환

#### 3.2 HTML 리포트 생성
- [ ] Jinja2 템플릿 설계
  - `templates/daily_report.html`: 메인 템플릿
  - `templates/sections/top_issues.html`: 주요 이슈 섹션
  - `templates/sections/winery.html`: 와이너리 섹션
  - `templates/sections/importer.html`: 수입사 섹션
  - `templates/sections/community.html`: 커뮤니티 섹션
  - `templates/components/card.html`: 링크 카드 컴포넌트
- [ ] html_reporter.py 구현
  - `generate_daily_report()`: 메인 생성 함수
  - 섹션별 ViewItem 렌더링
  - 통계 위젯 (일일 수집 건수, 인기 와이너리 등)
- [ ] CSS 스타일링
  - 반응형 디자인 (모바일 지원)
  - 다크모드 토글 (선택적)
- [ ] 리포트 파일 구조
  - `reports/YYYY/MM/YYYY-MM-DD.html`

**완료 조건**: HTML 리포트 생성 및 브라우저 확인

#### 3.3 GitHub Pages 배포
- [ ] gh-pages 브랜치 설정
- [ ] 인덱스 페이지 생성
  - 최근 30일 리포트 목록
  - 달력 형태 네비게이션
- [ ] GitHub Actions 워크플로우 수정
  - 리포트 생성 후 gh-pages 브랜치에 푸시
  - GitHub Pages 자동 배포
- [ ] 커스텀 도메인 설정 (선택적)

**완료 조건**: `https://<username>.github.io/WineRadar` 접속 가능

#### 3.4 스냅샷 기능
- [ ] snapshot.py 구현
  - `create_daily_snapshot()`: 일일 요약 생성
  - `create_monthly_snapshot()`: 월간 요약
  - 인기 와이너리/토픽 TOP 10
  - 트렌드 변화 감지
- [ ] 스냅샷 저장
  - `snapshots/daily/YYYY-MM-DD.json`
  - `snapshots/monthly/YYYY-MM.json`
- [ ] 스냅샷 조회 API (선택적)

**완료 조건**: 스냅샷 파일 생성 및 리포트에 통계 포함

### Phase 3 마일스톤
- ✅ 그래프 쿼리로 관점별 데이터 조회
- ✅ HTML 데일리 리포트 자동 생성
- ✅ GitHub Pages 자동 배포
- ✅ 일/월 스냅샷 기록

---

## Phase 4: 알림 및 최적화 (Week 8)

### 목표
알림 채널 구현 및 시스템 최적화

### 주요 작업

#### 4.1 Telegram Pusher
- [ ] telegram_pusher.py 구현
  - Telegram Bot API 연동
  - 데일리 리포트 요약 메시지
  - 주요 이슈 TOP 5 카드
  - 리포트 페이지 링크
- [ ] GitHub Secrets 설정
  - TELEGRAM_BOT_TOKEN
  - TELEGRAM_CHAT_ID
- [ ] 메시지 템플릿 디자인
- [ ] 테스트 (실제 전송 확인)

**완료 조건**: 텔레그램으로 데일리 요약 수신

#### 4.2 Email Pusher (선택적)
- [ ] email_pusher.py 구현
  - SMTP 또는 SendGrid 연동
  - HTML 이메일 템플릿
- [ ] 설정 및 테스트

**완료 조건**: 이메일 수신 확인

#### 4.3 성능 최적화
- [ ] 데이터베이스 쿼리 최적화
  - 인덱스 추가
  - 쿼리 프로파일링
- [ ] Collector 병렬 실행
  - ThreadPoolExecutor 활용
  - 타임아웃 설정
- [ ] 메모리 사용 최적화
  - 대량 데이터 배치 처리
- [ ] GitHub Actions 실행 시간 단축
  - 캐싱 활용

**완료 조건**: 전체 파이프라인 5분 이내 실행

#### 4.4 모니터링 및 알림
- [ ] 파이프라인 실패 시 알림
  - GitHub Actions 실패 시 이슈 생성
  - 또는 Telegram으로 에러 알림
- [ ] 헬스체크 대시보드 (선택적)
  - 최근 실행 상태
  - 수집 소스별 성공률
  - 그래프 크기 통계

**완료 조건**: 실패 시 자동 알림 수신

#### 4.5 문서 정리
- [ ] README.md 업데이트
  - 실행 방법
  - 설정 가이드
  - 스크린샷 추가
- [ ] 기여 가이드 작성 (선택적)
- [ ] 라이센스 명시

**완료 조건**: 신규 사용자가 README만으로 실행 가능

### Phase 4 마일스톤
- ✅ 텔레그램 알림 자동 발송
- ✅ 시스템 안정성 확보
- ✅ 문서 완성

---

## MVP 완성 기준

### 필수 기능
- [x] 매일 자동으로 와인 관련 링크 수집
- [x] 와인 관련 항목만 필터링
- [x] 와이너리/수입사 엔티티 추출
- [x] 그래프 스토어에 관계 저장
- [x] HTML 데일리 리포트 생성
- [x] GitHub Pages 자동 배포
- [x] 텔레그램 알림 발송
- [x] URL TTL 기반 자동 정리

### 성능 목표
- 5개 이상 소스에서 데이터 수집
- 엔티티 추출 정확도 80% 이상
- 전체 파이프라인 실행 시간 5분 이내
- 일일 리포트 로딩 속도 2초 이내

### 품질 목표
- 테스트 커버리지 70% 이상
- mypy 타입 체크 통과
- 주요 모듈 단위 테스트 작성
- 에러 로깅 및 복구 로직

---

## Post-MVP 확장 계획

### Phase 5: 고급 기능 (선택적)

#### 5.1 MCP 서버 구현
- wineradar.get_view 툴
- wineradar.top_entities 툴
- Claude Desktop 연동

#### 5.2 고급 분석
- 감성 분석 (긍정/부정 뉴스)
- 트렌드 변화 감지
- 와이너리 네트워크 시각화

#### 5.3 사용자 인터페이스
- 웹 대시보드 (React/Vue)
- 인터랙티브 그래프 탐색
- 알림 설정 UI

#### 5.4 데이터 확장
- 인스타그램/트위터 수집
- 와인 가격 정보 연동
- 평점 데이터 통합

---

## 리스크 및 대응 방안

### 기술적 리스크

#### 1. RSS 소스 변경/중단
- **대응**: 다양한 소스 확보, 파싱 에러 처리 강화
- **우선순위**: Medium

#### 2. GitHub Actions 실행 시간 초과
- **대응**: 병렬 처리, 캐싱, 무료 플랜 제한 모니터링
- **우선순위**: High

#### 3. 엔티티 추출 정확도 부족
- **대응**: 사전 확장, LLM 활용 (GPT-4 API, 선택적)
- **우선순위**: Medium

#### 4. 데이터베이스 크기 증가
- **대응**: pruning 주기 조정, 압축, 아카이빙
- **우선순위**: Low

### 운영 리스크

#### 1. 수동 설정 필요 (Telegram token 등)
- **대응**: 설정 가이드 문서화
- **우선순위**: Low

#### 2. 소스별 크롤링 정책 위반
- **대응**: rate limiting, robots.txt 준수, 공개 RSS만 사용
- **우선순위**: High

---

## 성공 지표 (KPI)

### 개발 단계
- [ ] Phase 1-4 일정 준수
- [ ] 테스트 커버리지 70% 달성
- [ ] 주요 버그 0건

### 운영 단계
- [ ] 30일 연속 자동 실행 성공
- [ ] 일평균 50개 이상 링크 수집
- [ ] 사용자 피드백 3건 이상 수집

### 품질 지표
- [ ] 엔티티 추출 정확도 80%
- [ ] 필터링 노이즈율 10% 이하
- [ ] 리포트 로딩 속도 2초 이내

---

## 다음 단계

1. **Phase 1 시작**: 개발 환경 설정 및 SQLite 구현
2. **주간 체크포인트**: 매주 금요일 진행 상황 리뷰
3. **이슈 트래킹**: GitHub Issues 활용

**최종 목표**: 8주 내 MVP 완성 및 실제 운영 시작
