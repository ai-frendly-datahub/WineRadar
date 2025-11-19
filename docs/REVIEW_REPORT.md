# WineRadar 문서 검토 보고서

**검토 일자**: 2025-01-19
**검토 대상**: 프로젝트 전체 문서 (11개 파일)
**검토자**: Claude Code

---

## 요약

| 항목 | 점수 |
|------|------|
| 문서 완성도 | 85/100 |
| 기술적 정확성 | 75/100 |
| 일관성 | 60/100 |
| 실용성 | 90/100 |
| **종합 점수** | **78/100** |

**핵심 발견**: 문서화 수준은 매우 높으나, API 스펙과 실제 코드 간 불일치가 주요 개선 포인트

---

## 발견된 이슈

### 🔴 Critical (즉시 수정 필요)

#### 1. API_SPEC.md와 실제 코드의 함수 시그니처 불일치

**영향도**: High - 개발자가 잘못된 API를 참조할 가능성

**상세 내용**:

##### 1-1. `graph_store.py` - `upsert_url_and_entities()` 함수

**API_SPEC.md** (라인 342-349):
```python
def upsert_url_and_entities(
    db_path: Path,           # ← 문서에만 존재
    item: FilteredItem,
    entities: list[Entity],
    score: float,            # ← 문서에만 존재
    source_weight: float,    # ← 문서에만 존재
    ttl_days: int = 30       # ← 문서에만 존재
) -> None:
```

**실제 코드** (`graph/graph_store.py`, 라인 29):
```python
def upsert_url_and_entities(item, entities, now: datetime) -> None:
    #                                         ↑ 코드에만 존재
```

**차이점**:
- `db_path` 파라미터 누락 (모든 graph 함수에서 동일)
- `score`, `source_weight`, `ttl_days` 파라미터 누락
- `now` 파라미터는 문서에 없음
- 타입 힌트 누락 (`item`, `entities`에 타입 없음)

##### 1-2. `graph_queries.py` - `get_view()` 함수

**API_SPEC.md** (라인 417-425):
```python
def get_view(
    db_path: Path,                      # ← 문서에만 존재
    view_type: Literal["winery", ...],
    focus_id: str | None = None,        # ← 기본값 있음
    time_window: timedelta = timedelta(days=7),  # ← 기본값 있음
    limit: int = 50,
    source_filter: list[str] | None = None
) -> list[ViewItem]:
```

**실제 코드** (`graph/graph_queries.py`, 라인 18-24):
```python
def get_view(
    view_type: Literal["winery", "importer", "wine", "topic", "community"],
    focus_id: str | None,               # ← 기본값 없음
    time_window: timedelta,             # ← 기본값 없음
    limit: int = 50,
    source_filter: list[str] | None = None,
) -> list[ViewItem]:
```

**차이점**:
- `db_path` 파라미터 누락
- `focus_id`, `time_window` 기본값이 문서와 코드에서 다름

##### 1-3. `graph_store.py` - `prune_expired_urls()` 함수

**API_SPEC.md** (라인 371-379):
```python
def prune_expired_urls(
    db_path: Path,        # ← 문서에만 존재
    now: datetime
) -> int:
```

**실제 코드** (`graph/graph_store.py`, 라인 39):
```python
def prune_expired_urls(now: datetime, ttl_days: int = 30) -> None:
    #                                  ↑ 코드에만 존재    ↑ 반환 타입 다름
```

**차이점**:
- `db_path` 파라미터 누락
- `ttl_days` 파라미터가 문서에 없음
- 반환 타입: 문서 `int` vs 코드 `None`

**권장 조치**:
1. **옵션 A**: API_SPEC.md를 실제 코드에 맞춰 수정 (빠른 해결)
2. **옵션 B**: 실제 코드를 API_SPEC.md에 맞춰 수정 (장기적으로 더 나은 설계)
   - `db_path` 파라미터를 추가하면 함수가 더 순수하고 테스트 가능
   - 글로벌 DB 연결 대신 명시적 경로 전달

**우선순위**: 🔴 Critical - Phase 1 구현 시작 전에 결정 필요

---

#### 2. ENCODING.md 파일이 사용자에 의해 간소화됨

**상태**: 사용자가 ENCODING.md를 9줄짜리 간결한 버전으로 교체함

**기존 버전** (433줄):
- UTF-8 인코딩 강제 방법 상세 설명
- EditorConfig, Git Attributes, VSCode 설정
- 인코딩 문제 해결 방법
- CI/CD 검증 워크플로우

**현재 버전** (9줄):
```markdown
# Encoding 정책

- 모든 소스 코드는 UTF-8 (BOM 없음) 으로 저장합니다.
- Windows 환경에서도 `git config core.autocrlf false` 를 권장...
- 문서 역시 UTF-8을 사용하며...
- 터미널 출력은 가능하면 ASCII/영문 로그를 사용...
- 외부에서 받은 TSV/CSV 파일을 사용할 경우...
```

**영향**:
- ✅ **긍정적**: 간결하고 핵심만 담음
- ⚠️ **부정적**: 트러블슈팅 가이드 손실
- ⚠️ **DEPLOYMENT.md**에서 ENCODING.md를 참조하는 부분이 더 이상 유효하지 않을 수 있음

**권장 조치**:
- 현재 버전 유지 (사용자 의도)
- DEPLOYMENT.md의 ENCODING.md 참조 섹션 업데이트

**우선순위**: 🔴 Critical - DEPLOYMENT.md 참조 확인 필요

---

#### 3. Phase 번호 불일치

**README.md** (라인 110):
```markdown
**현재 단계**: Phase 0 - 스타터 킷 (스켈레톤 코드)
```

**ROADMAP.md**:
- Phase 0 언급 없음
- Phase 1부터 시작 (Week 1-2)
- Phase 4까지 정의 (Total 8주)

**문제**:
- 현재 상태를 "Phase 0"로 부르는지 "구현 전 단계"로 부르는지 불명확
- ROADMAP.md를 따르면 Phase 1이 "기본 인프라 구축"인데, README에서 Phase 0라고 하면 혼란

**권장 조치**:
```markdown
**현재 단계**: 스켈레톤 코드 (구현 전)

다음 단계:
- [ ] Phase 1: 기본 인프라 (SQLite, 설정, 로깅)
```

**우선순위**: 🔴 Critical - 개발 진행 추적 혼란 방지

---

### 🟡 Important (조기 수정 권장)

#### 4. ROADMAP.md의 완료 체크박스 오류

**ROADMAP.md** (라인 318-327):
```markdown
### 필수 기능
- [x] 매일 자동으로 와인 관련 링크 수집
- [x] 와인 관련 항목만 필터링
- [x] 와이너리/수입사 엔티티 추출
- [x] 그래프 스토어에 관계 저장
- [x] HTML 데일리 리포트 생성
- [x] GitHub Pages 자동 배포
- [x] 텔레그램 알림 발송
- [x] URL TTL 기반 자동 정리
```

**실제 상태**:
- `main.py`: 스켈레톤 코드, `print()` 문만 있음
- `graph_store.py`: 모든 함수가 `raise NotImplementedError`
- `graph_queries.py`: 모든 함수가 `raise NotImplementedError`

**권장 조치**:
```markdown
### 필수 기능
- [ ] 매일 자동으로 와인 관련 링크 수집
- [ ] 와인 관련 항목만 필터링
- [ ] 와이너리/수입사 엔티티 추출
- [ ] 그래프 스토어에 관계 저장
- [ ] HTML 데일리 리포트 생성
- [ ] GitHub Pages 자동 배포
- [ ] 텔레그램 알림 발송
- [ ] URL TTL 기반 자동 정리
```

**우선순위**: 🟡 Important - 로드맵 신뢰성 확보

---

#### 5. `.github/workflows/crawler.yml` 파일 경로 문제

**DEPLOYMENT.md** (라인 228):
```markdown
[.github/workflows/crawler.yml](.github/workflows/crawler.yml) 업데이트:
```

**실제 상태**:
- `git status`에서 `.github/` 폴더가 새 파일로 표시됨
- 커밋 로그에 포함됨: `.github/workflows/crawler.yml`
- ✅ 파일 존재 확인됨

**결론**: 이슈 아님, 정상 상태

---

#### 6. `sources.yaml`의 예시 URL이 실제 사용 불가

**config/sources.yaml** (라인 12, 21, 30, 39):
```yaml
list_url: "https://example.com/wine21/rss"
list_url: "https://example.com/decanter/rss"
list_url: "https://example.com/importer/news"
list_url: "https://example.com/community/list"
```

**문제**:
- 모든 URL이 `example.com` (존재하지 않음)
- 실제 테스트/개발 불가능
- DEPLOYMENT.md (라인 201-223)에서 "실제 URL로 변경" 가이드 있으나 예시 없음

**권장 조치**:
최소한 1개의 실제 동작하는 공개 RSS 피드 추가:
```yaml
- name: "Decanter"
  id: "media_decanter"
  type: "media"
  country: "GLOBAL"
  enabled: true
  weight: 3.0
  config:
    list_url: "https://www.decanter.com/feed/"  # 실제 URL
```

**우선순위**: 🟡 Important - Phase 2 (데이터 수집) 시작 전 필수

---

#### 7. 문서 간 내부 링크 일관성 부족

**발견 사항**:
- 일부 문서는 상대 경로 사용: `docs/API_SPEC.md`
- 일부 문서는 절대 경로처럼 표기: `(docs/DEPLOYMENT.md)`
- 모든 링크가 동작하지만 표기 방식이 불일치

**예시**:
- **CODING_GUIDE.md** (라인 42): `docs/AI_TASK_TEMPLATE.md`
- **README.md** (라인 88-94): `(docs/ARCHITECTURE.md)`, `(docs/ROADMAP.md)` 등

**권장 조치**:
모든 문서에서 일관된 링크 형식 사용:
```markdown
[문서명](docs/FILENAME.md)
```

**우선순위**: 🟡 Important - 가독성 및 유지보수성

---

### 🟢 Minor (개선 권장)

#### 8. 용어 사용 일관성 부족

**발견 사항**:
- **한글**: "와이너리", "수입사", "토픽"
- **영문**: "winery", "importer", "topic"
- **혼용**: 문서 설명에서 한글, 코드에서 영문

**예시**:
- **DATA_MODEL.md** (라인 116): "와이너리 (예: Domaine DRC)"
- **코드** (`graph_queries.py`, 라인 19): `Literal["winery", "importer", ...]`

**현재 상태**: 사실상 일관적 (설명은 한글, 코드는 영문)

**권장 조치** (선택적):
문서에서 처음 언급 시 병기:
```markdown
- `winery`: 와이너리 (예: Domaine DRC, Château Margaux)
- `importer`: 수입사 (예: 금양인터내셔날, 롯데주류)
- `topic`: 토픽/키워드 (예: 내추럴와인, 부르고뉴)
```

**우선순위**: 🟢 Minor - 현재 상태도 충분히 이해 가능

---

#### 9. ARCHITECTURE.md가 너무 간결함

**현재 상태**:
- 총 35줄 (다른 문서 대비 매우 짧음)
- 레이어 구조, 핵심 개념, 메인 파이프라인 개요만 포함

**비교**:
- **DATA_MODEL.md**: 745줄 (매우 상세)
- **API_SPEC.md**: 1073줄 (매우 상세)

**누락 내용**:
- 시스템 아키텍처 다이어그램
- 데이터 흐름도
- 컴포넌트 간 상호작용
- 기술 스택 선택 이유

**권장 조치**:
```markdown
## 시스템 구성도

```
┌─────────────┐
│  GitHub     │
│  Actions    │ ─── 매일 00:00 UTC 실행
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────┐
│         WineRadar Pipeline              │
│                                         │
│  Collectors → Analyzers → Graph Store  │
│     ↓             ↓           ↓         │
│  RawItem    FilteredItem   Nodes/Edges │
│                                         │
│  Graph Store → Reporters → Pushers     │
│       ↓            ↓          ↓         │
│  ViewItems      HTML     Telegram      │
└─────────────────────────────────────────┘
       │
       v
┌──────────────┐
│ GitHub Pages │
│   (리포트)    │
└──────────────┘
```
```

**우선순위**: 🟢 Minor - 신규 개발자 온보딩 개선

---

#### 10. PRD.md 미완성 상태

**현재 상태** (19줄):
```markdown
# WineRadar PRD (Product Requirements Document)

## 1. 제품 개요
...

(이하 세부 내용은 대화에서 정리한 요구사항을 기반으로 작성/확장하면 됩니다.
MVP 범위, 타깃 유저, 주요 플로우, 비기능 요구사항 등을 여기에 단계적으로 채워 넣으세요.)
```

**누락 내용**:
- 타깃 유저 페르소나
- 주요 유스케이스
- 비기능 요구사항 (성능, 보안, 확장성)
- 경쟁 제품 분석
- 성공 지표

**권장 조치**:
```markdown
## 2. 타깃 유저

### 페르소나 1: 와인 애호가 (Enthusiast)
- 최신 와인 트렌드에 관심
- 특정 와이너리/수입사 팔로우
- 일일 뉴스 요약 필요

### 페르소나 2: 와인 수입사/유통사
- 경쟁사 동향 파악
- 인기 와이너리 추적
- 마케팅 인사이트 확보

## 3. 주요 유스케이스

### UC1: 일일 와인 뉴스 확인
1. 사용자가 매일 아침 GitHub Pages 접속
2. 전날 수집된 와인 뉴스 요약 확인
3. 관심 와이너리 섹션에서 상세 기사 클릭

### UC2: 특정 와이너리 트렌드 추적
...
```

**우선순위**: 🟢 Minor - MVP 기능 정의는 이미 ROADMAP.md에 있음

---

#### 11. MCP_SPEC.md와 API_SPEC.md 중복

**MCP_SPEC.md** (46줄):
- 간략한 MCP 툴 스키마만 정의
- 구현 방법 언급 없음

**API_SPEC.md** (라인 792-876):
- MCP Tools 스키마 상세 정의
- 구현 예시 코드 포함
- MCP Tool Handler 함수 시그니처

**문제**: 정보 중복, 일관성 유지 어려움

**권장 조치**:
- **옵션 A**: MCP_SPEC.md 삭제, API_SPEC.md에 통합
- **옵션 B**: MCP_SPEC.md를 확장하여 MCP 서버 구현 가이드로 활용

**우선순위**: 🟢 Minor - 현재는 MCP 서버가 선택적 기능

---

#### 12. DEPLOYMENT.md의 requirements.txt 중복 나열

**DEPLOYMENT.md** (라인 57-72):
```markdown
**requirements.txt** (업데이트 필요):
```
requests>=2.31.0
beautifulsoup4>=4.12.0
...
```
```

**실제 파일**: `d:\WineRadar\requirements.txt` 존재

**문제**:
- 파일 내용이 두 곳에 존재
- 수정 시 두 곳 모두 업데이트 필요
- 일관성 유지 어려움

**권장 조치**:
```markdown
**requirements.txt**:
프로젝트 루트의 `requirements.txt` 파일을 참고하세요.

주요 의존성:
- requests: HTTP 요청
- feedparser: RSS 파싱
- pyyaml: 설정 파일 로드
- jinja2: HTML 템플릿
```

**우선순위**: 🟢 Minor - DRY 원칙

---

#### 13. AI_TASK_TEMPLATE.md 활용도 부족

**현재 상태** (18줄):
- 간단한 작업 요청 템플릿만 제공
- 실제 사용 예시 없음

**CODING_GUIDE.md** (라인 42):
```markdown
- docs/AI_TASK_TEMPLATE.md 를 참고해 동일한 형식으로 요청
```

**문제**:
- 템플릿이 너무 추상적
- 실제 사용법 불명확

**권장 조치**:
실제 예시 추가:
```markdown
## 예시: RSS Collector 구현 요청

### 작업 설명
- 목적: Wine21 RSS 피드에서 최신 기사 수집
- 역할: RSSCollector 클래스 구현

### 입력/출력 규격
- 입력: feed_url (str), max_items (int)
- 출력: Iterable[RawItem]

### 제약
- 사용해야 하는 인터페이스: collectors/base.py의 Collector Protocol
- feedparser 라이브러리 사용
- 네트워크 에러는 로그만 남기고 빈 리스트 반환

### 완료 조건
- collectors/rss_collector.py 생성
- 단위 테스트 통과 (tests/unit/collectors/test_rss_collector.py)
```

**우선순위**: 🟢 Minor - AI 협업 효율성 향상

---

#### 14. 테스트 디렉토리와 문서 설명 불일치

**README.md** (라인 137-139):
```markdown
- `tests/unit/` : 단위 테스트
- `tests/integration/` : 통합 테스트
- `tests/e2e/` : E2E 테스트
```

**실제 상태**:
- 디렉토리 존재 ✓
- 스켈레톤 테스트 파일 존재 ✓
- 대부분 `__init__.py`만 있거나 `pytest.mark.xfail` 적용됨

**문제**:
- 문서에서 "테스트 실행 가능"처럼 보이지만 실제로는 스켈레톤

**권장 조치**:
```markdown
### 테스트

테스트 디렉토리 구조가 준비되어 있으며, Phase별 구현과 함께 점진적으로 추가됩니다:
- `tests/unit/` : 단위 테스트 (추가 예정)
- `tests/integration/` : 통합 테스트 (추가 예정)
- `tests/e2e/` : E2E 테스트 (추가 예정)

```bash
# 현재는 대부분 xfail로 마킹되어 있음
pytest tests/unit  # 스켈레톤 확인용
```
```

**우선순위**: 🟢 Minor - 명확성 개선

---

## 잘된 점

### ✅ 1. 매우 상세한 DATA_MODEL.md (745줄)

**강점**:
- RawItem부터 ViewItem까지 모든 데이터 타입 명확히 정의
- SQLite 스키마 포함 (`CREATE TABLE` 문)
- 실제 예시 데이터 제공 (라인 650-734)
- TTL, 스코어링 알고리즘까지 상세 설명

**코드와의 일치성**:
```python
# DATA_MODEL.md (라인 18-28)
class RawItem(TypedDict):
    id: str
    url: str
    title: str
    summary: str | None
    content: str | None
    published_at: datetime
    source_name: str
    source_type: str
    language: str | None

# collectors/base.py (라인 7-17) - 완전히 일치 ✓
```

**평가**: 🌟🌟🌟🌟🌟 (5/5) - 모범 사례

---

### ✅ 2. 포괄적인 API_SPEC.md (1073줄)

**강점**:
- 모든 모듈의 API 상세 설명
- 함수 시그니처, 파라미터, 반환 타입
- 실제 사용 예시 코드 포함
- End-to-End 플로우 예시 (라인 992-1063)
- 에러 처리 전략 (라인 730-756)

**특히 우수한 부분**:
```python
# 사용 예시가 매우 구체적
# API_SPEC.md (라인 458-470)
drc_items = get_view(
    db_path=Path("wineradar.db"),
    view_type="winery",
    focus_id="winery_drc",
    time_window=timedelta(days=7),
    limit=20
)

top_wineries = get_top_entities(
    db_path=Path("wineradar.db"),
    entity_type="winery",
    time_window=timedelta(days=7),
    limit=10
)
```

**평가**: 🌟🌟🌟🌟🌟 (5/5) - Critical 이슈(함수 시그니처 불일치)만 해결하면 완벽

---

### ✅ 3. 실용적인 DEPLOYMENT.md (712줄)

**강점**:
- 로컬 개발부터 GitHub Actions 배포까지 전체 커버
- 단계별 명령어 제공
- 트러블슈팅 섹션 (라인 396-475)
- 체크리스트 (라인 629-661)
- Telegram Bot 생성 가이드 (라인 184-195)

**실용성 예시**:
```markdown
## 6.1 일반적인 문제

#### 문제 1: GitHub Actions 실행 실패
**증상**: Actions 탭에서 빨간색 ❌ 표시
**해결 방법**:
1. 로그 확인 (Actions → 실패한 워크플로우 클릭)
2. 에러 메시지 확인
3. 일반적인 원인:
   - 의존성 설치 실패 → requirements.txt 확인
   - 코드 에러 → 로컬에서 `python main.py` 테스트
   - Secrets 누락 → Settings → Secrets 확인
```

**평가**: 🌟🌟🌟🌟🌟 (5/5) - 신규 사용자도 쉽게 따라할 수 있음

---

### ✅ 4. 명확한 8주 ROADMAP (425줄)

**강점**:
- Phase 1-4 구체적 작업 정의
- 각 Phase별 목표, 완료 조건, 마일스톤
- 주간 일정 제시 (Phase 1: 2주, Phase 2: 3주 등)
- Post-MVP 확장 계획 (라인 342-365)
- 리스크 대응 방안 (라인 368-395)
- 성공 지표 (라인 398-417)

**평가**: 🌟🌟🌟🌟 (4/5) - 완료 체크박스 오류만 수정하면 완벽

---

### ✅ 5. 체계적인 엔티티 사전 구조

**강점**:
- `config/entities/wineries.yaml` 스키마 정의 (DATA_MODEL.md 라인 550-573)
- 별칭(aliases) 지원으로 다양한 표기 인식
- 국가, 지역, 공식 URL 메타데이터 포함

**예시**:
```yaml
wineries:
  - id: winery_drc
    name: Domaine de la Romanée-Conti
    aliases:
      - DRC
      - 로마네 콩티
      - 도메느 드 라 로마네 콩티
    country: France
    region: Burgundy
    official_url: https://www.romanee-conti.fr
```

**평가**: 🌟🌟🌟🌟🌟 (5/5) - 확장 가능하고 유지보수 용이

---

### ✅ 6. Protocol 기반 인터페이스 설계

**강점**:
- `collectors/base.py`의 `Collector` Protocol (라인 19-29)
- Duck typing 지원으로 다양한 Collector 쉽게 추가
- API_SPEC.md에서 Protocol 사용법 상세 설명 (라인 11-38)

```python
class Collector(Protocol):
    source_name: str
    source_type: str

    def collect(self) -> Iterable[RawItem]:
        """해당 소스에서 RawItem 시퀀스를 수집한다."""
        ...
```

**평가**: 🌟🌟🌟🌟🌟 (5/5) - Python다운 설계

---

### ✅ 7. 일관된 디렉토리 구조

**ARCHITECTURE.md 정의**:
```
collectors/ → analyzers/ → graph/ → reporters/ → pushers/
```

**실제 구조**: 완전히 일치 ✓

**평가**: 🌟🌟🌟🌟🌟 (5/5)

---

### ✅ 8. 설정 파일 주석 및 가이드

**config.yaml**:
```yaml
mode: daily                 # daily / incremental 등 (MVP에선 daily 위주)
timezone: Asia/Seoul

graph:
  url_ttl_days: 30          # URL 노드 보존 기간
  snapshot_keep_days: 30    # 일간 스냅샷 보존 기간
  monthly_keep_months: 12   # 월간 요약 보존 기간
```

**평가**: 🌟🌟🌟🌟 (4/5) - 주석이 명확함

---

### ✅ 9. UTF-8 인코딩 강제 설정

**구현 현황**:
- `.editorconfig` ✓
- `.gitattributes` ✓
- `.vscode/settings.json` ✓
- 모든 Python 파일에 `# -*- coding: utf-8 -*-` 선언 ✓

**ENCODING.md**: 사용자에 의해 간소화되었지만 핵심 정책은 유지됨

**평가**: 🌟🌟🌟🌟🌟 (5/5) - 인코딩 문제 사전 방지

---

### ✅ 10. MCP 서버 확장성 고려

**준비 상황**:
- `mcp_server/server_stub.py` 스켈레톤 ✓
- `mcp_server/manifest.json` 스키마 정의 ✓
- MCP_SPEC.md 초안 ✓
- API_SPEC.md에 MCP Tools 상세 설명 (라인 792-876) ✓

**평가**: 🌟🌟🌟🌟 (4/5) - 향후 확장 준비 완료

---

## 종합 평가

### 점수 세부 내역

| 카테고리 | 점수 | 근거 |
|----------|------|------|
| **문서 완성도** | 85/100 | DATA_MODEL, API_SPEC, DEPLOYMENT는 완벽. PRD, MCP_SPEC는 미완성 (-15) |
| **기술적 정확성** | 75/100 | API 스펙과 코드 불일치 (-20), 로드맵 체크박스 오류 (-5) |
| **일관성** | 60/100 | Phase 번호 불일치 (-10), 문서 간 링크 불일치 (-10), 용어 혼용 (-20) |
| **실용성** | 90/100 | 트러블슈팅, 체크리스트, 예시 코드 풍부. sources.yaml 예시 URL 문제 (-10) |
| **구조/가독성** | 88/100 | 대부분 우수. ARCHITECTURE.md 간결함 (-7), 테이블 형식 일부 개선 여지 (-5) |
| **종합 점수** | **78/100** | Critical 이슈 해결 시 **90+** 달성 가능 |

---

### 개선 우선순위

#### 🔴 즉시 (1일 내)
1. **API_SPEC.md와 코드 시그니처 통일**
   - 옵션 A: API_SPEC.md를 코드에 맞춰 수정 (빠름)
   - 옵션 B: 코드를 API_SPEC.md에 맞춰 수정 (장기적으로 더 나음)
2. **README.md Phase 번호 수정**: "Phase 0" → "스켈레톤 코드 (구현 전)"
3. **DEPLOYMENT.md의 ENCODING.md 참조 확인**: 새로운 간소화된 버전 반영

#### 🟡 단기 (1주 내)
4. **ROADMAP.md 완료 체크박스**: `[x]` → `[ ]`로 변경
5. **sources.yaml에 실제 RSS URL 추가**: 최소 1개 (예: Decanter)
6. **문서 간 링크 형식 통일**: `(docs/FILENAME.md)` 형식으로 표준화

#### 🟢 중기 (1개월 내)
7. **PRD.md 완성**: 타깃 유저, 유스케이스, 비기능 요구사항
8. **ARCHITECTURE.md 확장**: 시스템 다이어그램, 데이터 흐름도 추가
9. **MCP_SPEC.md와 API_SPEC.md 통합** 또는 MCP_SPEC.md 확장
10. **AI_TASK_TEMPLATE.md 예시 추가**: 실제 작업 요청 사례

---

### 최종 의견

**WineRadar 프로젝트는 문서화 수준이 매우 높습니다.** 특히 DATA_MODEL.md, API_SPEC.md, DEPLOYMENT.md는 상업 프로젝트 수준입니다.

**주요 개선 포인트**:
1. API 스펙과 코드 일치시키기 (Critical)
2. 로드맵 진행 상황 정확히 반영 (Important)
3. 실제 사용 가능한 예시 데이터/URL 제공 (Important)

**이 3가지만 해결하면 90/100 이상의 우수한 문서 품질을 달성할 수 있습니다.**

---

## 부록: 문서별 요약

| 문서 | 줄수 | 완성도 | 정확성 | 평점 |
|------|------|--------|--------|------|
| README.md | - | 80% | 70% | ⭐⭐⭐⭐ |
| ARCHITECTURE.md | 35 | 60% | 100% | ⭐⭐⭐ |
| PRD.md | 19 | 30% | 100% | ⭐⭐ |
| ROADMAP.md | 425 | 95% | 80% | ⭐⭐⭐⭐ |
| DATA_MODEL.md | 745 | 100% | 100% | ⭐⭐⭐⭐⭐ |
| API_SPEC.md | 1073 | 100% | 70% | ⭐⭐⭐⭐ |
| DEPLOYMENT.md | 712 | 100% | 95% | ⭐⭐⭐⭐⭐ |
| CODING_GUIDE.md | 42 | 90% | 100% | ⭐⭐⭐⭐ |
| ENCODING.md | 9 | 70% | 100% | ⭐⭐⭐⭐ |
| MCP_SPEC.md | 46 | 50% | 100% | ⭐⭐⭐ |
| AI_TASK_TEMPLATE.md | 18 | 60% | 100% | ⭐⭐⭐ |

---

**검토 완료**
