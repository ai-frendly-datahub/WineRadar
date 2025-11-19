# WineRadar API 스펙

## 개요

WineRadar의 주요 모듈별 API 인터페이스를 정의합니다. MVP에서는 내부 Python API로 사용하며, 향후 REST API 또는 MCP 서버로 확장 가능합니다.

---

## 1. Collector API

### 1.1 Collector 프로토콜

**파일**: `collectors/base.py`

```python
from typing import Protocol, Iterable

class Collector(Protocol):
    """외부 소스에서 링크를 수집하는 인터페이스"""

    source_name: str      # 소스 이름 (예: "Wine21")
    source_type: str      # 소스 타입: media, importer, community

    def collect(self) -> Iterable[RawItem]:
        """RawItem 시퀀스를 수집한다.

        Returns:
            Iterable[RawItem]: 수집된 원본 아이템들

        Raises:
            CollectorError: 수집 중 복구 불가능한 에러 발생 시

        Notes:
            - 개별 아이템 파싱 실패는 로그하고 건너뛴다
            - 네트워크 에러는 재시도 후 실패 시 빈 리스트 반환
        """
        ...
```

---

### 1.2 RSSCollector 구현 예시

**파일**: `collectors/rss_collector.py`

```python
class RSSCollector:
    """RSS 피드 기반 Collector"""

    def __init__(
        self,
        source_name: str,
        source_type: str,
        feed_url: str,
        timeout: int = 30,
        max_items: int = 100
    ):
        """
        Args:
            source_name: 소스 이름
            source_type: 소스 타입 (media/importer/community)
            feed_url: RSS 피드 URL
            timeout: 요청 타임아웃 (초)
            max_items: 최대 수집 아이템 수
        """
        ...

    def collect(self) -> Iterable[RawItem]:
        """RSS 피드를 파싱하여 RawItem 생성"""
        ...
```

**사용 예시**:

```python
collector = RSSCollector(
    source_name="Wine21",
    source_type="media",
    feed_url="https://wine21.com/rss"
)

for item in collector.collect():
    print(item["title"])
```

---

### 1.3 CollectorFactory

**파일**: `collectors/factory.py`

```python
def create_collectors(sources_config: list[dict]) -> list[Collector]:
    """sources.yaml 설정으로부터 Collector 인스턴스 생성

    Args:
        sources_config: sources.yaml의 sources 리스트

    Returns:
        list[Collector]: 활성화된 Collector 목록

    Example:
        >>> config = load_sources_config()
        >>> collectors = create_collectors(config["sources"])
        >>> for collector in collectors:
        ...     items = collector.collect()
    """
    ...
```

---

## 2. Analyzer API

### 2.1 KeywordFilter

**파일**: `analyzers/keyword_filter.py`

```python
class KeywordFilter:
    """키워드 기반 필터링"""

    def __init__(self, keywords_file: Path):
        """
        Args:
            keywords_file: frequency_words.txt 경로
        """
        ...

    def filter(self, items: Iterable[RawItem]) -> Iterable[FilteredItem]:
        """RawItem을 필터링하여 와인 관련 항목만 통과

        Args:
            items: 원본 아이템들

        Yields:
            FilteredItem: 필터를 통과한 아이템

        Filtering Rules:
            - 일반 키워드: 하나라도 매칭되면 통과
            - 필수 키워드(+): 하나 이상 필수
            - 제외 키워드(!): 포함 시 필터링
        """
        ...

    def _calculate_confidence(self, item: RawItem, matched: list[str]) -> float:
        """와인 관련도 점수 계산 (0.0 ~ 1.0)"""
        ...
```

**사용 예시**:

```python
filter = KeywordFilter(Path("config/frequency_words.txt"))
filtered = filter.filter(raw_items)

for item in filtered:
    print(f"{item['raw_item']['title']} - confidence: {item['confidence']}")
```

---

### 2.2 EntityExtractor

**파일**: `analyzers/entity_extractor.py`

```python
class EntityExtractor:
    """엔티티 추출기 (와이너리, 수입사, 토픽 등)"""

    def __init__(
        self,
        wineries_dict: dict,
        importers_dict: dict,
        topics_dict: dict
    ):
        """
        Args:
            wineries_dict: wineries.yaml 로드 결과
            importers_dict: importers.yaml 로드 결과
            topics_dict: topics.yaml 로드 결과
        """
        ...

    def extract(self, item: FilteredItem) -> list[Entity]:
        """FilteredItem에서 엔티티 추출

        Args:
            item: 필터링된 아이템

        Returns:
            list[Entity]: 추출된 엔티티 목록 (중복 제거됨)

        Extraction Methods:
            - 사전 매칭 (정확 일치 + 별칭)
            - 패턴 매칭 (정규식)
            - 신뢰도 점수 부여
        """
        ...

    def _match_wineries(self, text: str) -> list[Entity]:
        """와이너리 매칭"""
        ...

    def _match_importers(self, text: str) -> list[Entity]:
        """수입사 매칭"""
        ...

    def _match_topics(self, text: str) -> list[Entity]:
        """토픽 매칭"""
        ...
```

**사용 예시**:

```python
extractor = EntityExtractor(
    wineries_dict=load_yaml("config/entities/wineries.yaml"),
    importers_dict=load_yaml("config/entities/importers.yaml"),
    topics_dict=load_yaml("config/entities/topics.yaml")
)

for filtered_item in filtered_items:
    entities = extractor.extract(filtered_item)
    print(f"Found entities: {[e['name'] for e in entities]}")
```

---

### 2.3 Scoring

**파일**: `analyzers/scoring.py`

```python
def calculate_score(
    item: FilteredItem,
    entities: list[Entity],
    source_weight: float,
    now: datetime | None = None
) -> float:
    """종합 점수 계산

    Args:
        item: 필터링된 아이템
        entities: 추출된 엔티티 목록
        source_weight: 소스 가중치 (sources.yaml)
        now: 현재 시각 (테스트용, None이면 자동)

    Returns:
        float: 종합 점수 (0.0 ~ 10.0)

    Scoring Formula:
        score = source_weight × freshness × entity_boost × 10.0

        - source_weight: 소스 가중치 (0.0 ~ 3.0)
        - freshness: 신선도 (최근 7일 기준, 1.0 → 0.0)
        - entity_boost: 엔티티 가산점 (1.0 ~ 1.5)
    """
    ...
```

---

### 2.4 Snapshot

**파일**: `analyzers/snapshot.py`

```python
def create_daily_snapshot(date: date, db_path: Path) -> dict:
    """일일 스냅샷 생성

    Args:
        date: 대상 날짜
        db_path: SQLite DB 경로

    Returns:
        dict: 스냅샷 데이터
        {
            "date": "2025-01-19",
            "total_urls": 123,
            "total_entities": 45,
            "top_wineries": [{"id": "...", "name": "...", "count": 10}, ...],
            "top_topics": [...],
            "sources_stats": {"Wine21": 50, "Decanter": 30, ...}
        }
    """
    ...

def create_monthly_snapshot(year: int, month: int, db_path: Path) -> dict:
    """월간 스냅샷 생성 (일일 스냅샷 집계)

    Args:
        year: 연도
        month: 월
        db_path: SQLite DB 경로

    Returns:
        dict: 월간 요약
    """
    ...

def save_snapshot(snapshot: dict, output_path: Path) -> None:
    """스냅샷을 JSON 파일로 저장"""
    ...
```

---

## 3. Graph API

### 3.1 GraphStore

**파일**: `graph/graph_store.py`

```python
def init_database(db_path: Path) -> None:
    """데이터베이스 초기화 (테이블 생성)

    Args:
        db_path: SQLite 파일 경로
    """
    ...

def upsert_node(db_path: Path, node: Node) -> None:
    """노드 삽입 또는 업데이트

    Args:
        db_path: SQLite 파일 경로
        node: 노드 데이터
    """
    ...

def upsert_edge(db_path: Path, edge: Edge) -> None:
    """엣지 삽입 또는 업데이트

    Args:
        db_path: SQLite 파일 경로
        edge: 엣지 데이터
    """
    ...

def upsert_url_and_entities(
    db_path: Path,
    item: FilteredItem,
    entities: list[Entity],
    score: float,
    source_weight: float,
    ttl_days: int = 30
) -> None:
    """URL 및 관련 엔티티를 그래프에 저장 (트랜잭션)

    Args:
        db_path: SQLite 파일 경로
        item: 필터링된 아이템
        entities: 추출된 엔티티
        score: 계산된 점수
        source_weight: 소스 가중치
        ttl_days: URL TTL (일)

    Process:
        1. URL 노드 생성/업데이트
        2. 엔티티 노드 생성/업데이트 (별칭 병합)
        3. URL → 엔티티 엣지 생성/업데이트
    """
    ...

def prune_expired_urls(db_path: Path, now: datetime) -> int:
    """만료된 URL 노드 및 관련 엣지 삭제

    Args:
        db_path: SQLite 파일 경로
        now: 현재 시각

    Returns:
        int: 삭제된 URL 수
    """
    ...

def get_nodes_by_type(
    db_path: Path,
    node_type: str,
    limit: int | None = None
) -> list[Node]:
    """타입별 노드 조회

    Args:
        db_path: SQLite 파일 경로
        node_type: 노드 타입 (url, winery, importer, topic, wine, community)
        limit: 최대 개수 (None이면 전체)

    Returns:
        list[Node]: 노드 목록
    """
    ...

def get_database_stats(db_path: Path) -> dict:
    """데이터베이스 통계

    Returns:
        {
            "total_nodes": 1234,
            "nodes_by_type": {"url": 1000, "winery": 100, ...},
            "total_edges": 3456,
            "db_size_mb": 12.5
        }
    """
    ...
```

---

### 3.2 GraphQueries

**파일**: `graph/graph_queries.py`

```python
def get_view(
    db_path: Path,
    view_type: Literal["winery", "importer", "wine", "topic", "community"],
    focus_id: str | None = None,
    time_window: timedelta = timedelta(days=7),
    limit: int = 50,
    source_filter: list[str] | None = None
) -> list[ViewItem]:
    """특정 관점(view)으로 URL 목록 조회

    Args:
        db_path: SQLite 파일 경로
        view_type: 뷰 타입
        focus_id: 중심 엔티티 ID (None이면 전체 TOP)
        time_window: 시간 범위 (최근 N일)
        limit: 최대 개수
        source_filter: 소스 필터 (예: ["Wine21", "Decanter"])

    Returns:
        list[ViewItem]: ViewItem 목록 (score 내림차순 정렬)

    View Types:
        - winery: 특정 와이너리 관련 링크
        - importer: 특정 수입사 관련 링크
        - topic: 특정 토픽 관련 링크
        - community: 커뮤니티 소스만
        - wine: 특정 와인 관련 링크
    """
    ...

def get_top_entities(
    db_path: Path,
    entity_type: Literal["winery", "importer", "topic", "wine"],
    time_window: timedelta = timedelta(days=7),
    limit: int = 10
) -> list[dict]:
    """인기 엔티티 조회 (링크 언급 횟수 기준)

    Args:
        db_path: SQLite 파일 경로
        entity_type: 엔티티 타입
        time_window: 시간 범위
        limit: 최대 개수

    Returns:
        list[dict]: [{"id": "...", "name": "...", "count": 10, "score": 8.5}, ...]
    """
    ...

def get_daily_stats(
    db_path: Path,
    date: date
) -> dict:
    """특정 날짜의 통계

    Args:
        db_path: SQLite 파일 경로
        date: 대상 날짜

    Returns:
        dict: {
            "total_urls": 123,
            "sources": {"Wine21": 50, ...},
            "entities": {"winery": 30, "topic": 45, ...}
        }
    """
    ...
```

**사용 예시**:

```python
# 최근 7일 DRC 관련 링크
drc_items = get_view(
    db_path=Path("wineradar.db"),
    view_type="winery",
    focus_id="winery_drc",
    time_window=timedelta(days=7),
    limit=20
)

# 최근 7일 인기 와이너리 TOP 10
top_wineries = get_top_entities(
    db_path=Path("wineradar.db"),
    entity_type="winery",
    time_window=timedelta(days=7),
    limit=10
)
```

---

## 4. Reporter API

### 4.1 HTMLReporter

**파일**: `reporters/html_reporter.py`

```python
def generate_daily_report(
    target_date: date,
    sections: dict[str, list[ViewItem]],
    stats: dict[str, Any],
    output_path: Path,
    template_dir: Path = Path("templates")
) -> Path:
    """데일리 HTML 리포트 생성

    Args:
        target_date: 대상 날짜
        sections: 섹션별 ViewItem
            {
                "top_issues": [...],
                "winery": [...],
                "importer": [...],
                "community": [...]
            }
        stats: 통계 데이터
            {
                "total_urls": 123,
                "top_wineries": [...],
                "sources": {...}
            }
        output_path: 출력 파일 경로
        template_dir: Jinja2 템플릿 디렉토리

    Returns:
        Path: 생성된 파일 경로

    Templates:
        - daily_report.html: 메인 템플릿
        - sections/*.html: 섹션별 템플릿
        - components/*.html: 재사용 컴포넌트
    """
    ...

def generate_index_page(
    reports: list[dict],
    output_path: Path,
    template_dir: Path = Path("templates")
) -> Path:
    """리포트 목록 인덱스 페이지 생성

    Args:
        reports: [{"date": "2025-01-19", "path": "reports/...", "stats": {...}}, ...]
        output_path: 출력 경로
        template_dir: 템플릿 디렉토리

    Returns:
        Path: 생성된 파일 경로
    """
    ...
```

---

## 5. Pusher API

### 5.1 TelegramPusher

**파일**: `pushers/telegram_pusher.py`

```python
class TelegramPusher:
    """Telegram Bot API를 통한 알림 발송"""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Args:
            bot_token: Telegram Bot Token
            chat_id: 대상 Chat ID
        """
        ...

    def send_daily_summary(
        self,
        date: date,
        top_items: list[ViewItem],
        stats: dict,
        report_url: str
    ) -> bool:
        """데일리 요약 발송

        Args:
            date: 대상 날짜
            top_items: 주요 이슈 (TOP 5)
            stats: 통계
            report_url: 리포트 페이지 URL

        Returns:
            bool: 발송 성공 여부

        Message Format:
            📊 WineRadar Daily Report - 2025-01-19

            🔥 Top Issues:
            1. DRC, 2024 빈티지 평가 '탁월'
            2. 샤또 마고, 신규 빈티지 출시
            ...

            📈 Today's Stats:
            - Total Links: 123
            - Top Winery: Domaine DRC (10)

            🔗 Full Report: https://...
        """
        ...

    def send_error_alert(self, error_message: str) -> bool:
        """에러 알림 발송"""
        ...
```

---

### 5.2 EmailPusher (선택적)

**파일**: `pushers/email_pusher.py`

```python
class EmailPusher:
    """SMTP 기반 이메일 발송"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str
    ):
        ...

    def send_daily_summary(
        self,
        to_addrs: list[str],
        date: date,
        html_content: str
    ) -> bool:
        """HTML 이메일 발송"""
        ...
```

---

## 6. Config API

### 6.1 ConfigLoader

**파일**: `config/loader.py`

```python
from pydantic import BaseModel

class GraphConfig(BaseModel):
    url_ttl_days: int = 30
    snapshot_keep_days: int = 30
    monthly_keep_months: int = 12

class ReportConfig(BaseModel):
    daily_max_items: int = 50
    sections: list[str]

class PushConfig(BaseModel):
    email: dict
    telegram: dict

class WineRadarConfig(BaseModel):
    mode: str
    timezone: str
    graph: GraphConfig
    report: ReportConfig
    push: PushConfig

def load_config(config_path: Path = Path("config/config.yaml")) -> WineRadarConfig:
    """설정 파일 로드 및 검증

    Args:
        config_path: config.yaml 경로

    Returns:
        WineRadarConfig: 검증된 설정 객체

    Raises:
        ValidationError: 설정 검증 실패 시
    """
    ...

def load_sources_config(sources_path: Path = Path("config/sources.yaml")) -> list[dict]:
    """소스 설정 로드

    Returns:
        list[dict]: 소스 목록
    """
    ...

def load_entity_dict(entity_path: Path) -> dict:
    """엔티티 사전 로드 (wineries.yaml, importers.yaml, topics.yaml)

    Args:
        entity_path: 엔티티 YAML 파일 경로

    Returns:
        dict: 엔티티 사전
            {
                "winery_drc": {
                    "id": "winery_drc",
                    "name": "Domaine de la Romanée-Conti",
                    "aliases": [...],
                    ...
                },
                ...
            }
    """
    ...
```

---

## 7. Main Pipeline API

### 7.1 메인 파이프라인

**파일**: `main.py`

```python
def run_once(
    config: WineRadarConfig,
    db_path: Path,
    output_dir: Path
) -> dict:
    """WineRadar 파이프라인 1회 실행

    Args:
        config: 설정 객체
        db_path: SQLite DB 경로
        output_dir: 리포트 출력 디렉토리

    Returns:
        dict: 실행 결과 통계
            {
                "collected": 150,
                "filtered": 120,
                "stored": 115,
                "report_path": "reports/2025-01-19.html",
                "duration_seconds": 45.3
            }

    Pipeline Steps:
        1. Config 로드
        2. Collector 실행 → RawItem[]
        3. 키워드 필터링 → FilteredItem[]
        4. 엔티티 추출 → (FilteredItem, Entity[])[]
        5. 스코어링 및 그래프 저장
        6. View 쿼리 → ViewItem[]
        7. HTML 리포트 생성
        8. Pusher 알림 발송
        9. 만료 URL 정리
        10. 스냅샷 생성
    """
    ...

def main():
    """CLI 엔트리포인트"""
    config = load_config()
    db_path = Path("wineradar.db")
    output_dir = Path("reports")

    result = run_once(config, db_path, output_dir)
    print(f"✅ Completed: {result}")
```

---

## 8. MCP 서버 API (선택적)

### 8.1 MCP Tools

**파일**: `mcp_server/server.py`

```python
# MCP Tool: wineradar.get_view
{
    "name": "wineradar.get_view",
    "description": "그래프에서 특정 관점의 와인 이슈 조회",
    "input_schema": {
        "type": "object",
        "properties": {
            "view_type": {
                "type": "string",
                "enum": ["winery", "importer", "wine", "topic", "community"],
                "description": "뷰 타입"
            },
            "focus_id": {
                "type": "string",
                "description": "엔티티 ID (예: winery_drc). 없으면 전체 TOP"
            },
            "time_window_days": {
                "type": "integer",
                "default": 7,
                "description": "최근 N일"
            },
            "limit": {
                "type": "integer",
                "default": 20,
                "description": "최대 개수"
            }
        },
        "required": ["view_type"]
    }
}

# MCP Tool: wineradar.top_entities
{
    "name": "wineradar.top_entities",
    "description": "인기 엔티티 조회",
    "input_schema": {
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "enum": ["winery", "importer", "topic", "wine"]
            },
            "time_window_days": {
                "type": "integer",
                "default": 7
            },
            "limit": {
                "type": "integer",
                "default": 10
            }
        },
        "required": ["entity_type"]
    }
}
```

**구현**:

```python
async def handle_get_view(params: dict) -> list[dict]:
    """MCP Tool Handler: wineradar.get_view"""
    view_items = get_view(
        db_path=Path("wineradar.db"),
        view_type=params["view_type"],
        focus_id=params.get("focus_id"),
        time_window=timedelta(days=params.get("time_window_days", 7)),
        limit=params.get("limit", 20)
    )
    return [dict(item) for item in view_items]

async def handle_top_entities(params: dict) -> list[dict]:
    """MCP Tool Handler: wineradar.top_entities"""
    return get_top_entities(
        db_path=Path("wineradar.db"),
        entity_type=params["entity_type"],
        time_window=timedelta(days=params.get("time_window_days", 7)),
        limit=params.get("limit", 10)
    )
```

---

## 9. 에러 처리

### 9.1 커스텀 예외

**파일**: `utils/exceptions.py`

```python
class WineRadarError(Exception):
    """Base exception"""

class CollectorError(WineRadarError):
    """Collector 관련 에러"""

class FilterError(WineRadarError):
    """필터링 에러"""

class GraphStoreError(WineRadarError):
    """그래프 스토어 에러"""

class ReporterError(WineRadarError):
    """리포트 생성 에러"""

class PusherError(WineRadarError):
    """알림 발송 에러"""
```

---

### 9.2 재시도 전략

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_rss_feed(url: str) -> feedparser.FeedParserDict:
    """RSS 피드 가져오기 (재시도 3회)"""
    ...
```

---

## 10. 테스트 API

### 10.1 테스트 픽스처

**파일**: `tests/conftest.py`

```python
import pytest

@pytest.fixture
def sample_raw_item() -> RawItem:
    """테스트용 RawItem"""
    return RawItem(
        id="test_001",
        url="https://example.com/test",
        title="Test Wine Article",
        summary="Test summary",
        content=None,
        published_at=datetime(2025, 1, 19, 10, 0, 0),
        source_name="TestSource",
        source_type="media",
        language="ko"
    )

@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """임시 SQLite DB"""
    db_path = tmp_path / "test.db"
    init_database(db_path)
    return db_path

@pytest.fixture
def mock_collector() -> Collector:
    """Mock Collector"""
    ...
```

---

### 10.2 단위 테스트 예시

**파일**: `tests/test_keyword_filter.py`

```python
def test_filter_with_positive_keywords(sample_raw_item):
    """긍정 키워드 매칭 테스트"""
    filter = KeywordFilter(Path("config/frequency_words.txt"))

    sample_raw_item["title"] = "DRC 와인 신규 출시"
    filtered = list(filter.filter([sample_raw_item]))

    assert len(filtered) == 1
    assert filtered[0]["confidence"] > 0.8

def test_filter_with_exclude_keywords(sample_raw_item):
    """제외 키워드 테스트"""
    filter = KeywordFilter(Path("config/frequency_words.txt"))

    sample_raw_item["title"] = "와인색 페인트 출시"  # "와인색" = 제외 키워드
    filtered = list(filter.filter([sample_raw_item]))

    assert len(filtered) == 0
```

---

## 부록: API 호출 체인 예시

### End-to-End 플로우

```python
# 1. 설정 로드
config = load_config()
sources = load_sources_config()

# 2. Collector 생성 및 실행
collectors = create_collectors(sources)
raw_items = []
for collector in collectors:
    raw_items.extend(collector.collect())

# 3. 필터링
filter = KeywordFilter(Path("config/frequency_words.txt"))
filtered_items = list(filter.filter(raw_items))

# 4. 엔티티 추출
extractor = EntityExtractor(
    wineries_dict=load_entity_dict(Path("config/entities/wineries.yaml")),
    importers_dict=load_entity_dict(Path("config/entities/importers.yaml")),
    topics_dict=load_entity_dict(Path("config/entities/topics.yaml"))
)

items_with_entities = []
for item in filtered_items:
    entities = extractor.extract(item)
    items_with_entities.append((item, entities))

# 5. 스코어링 및 저장
db_path = Path("wineradar.db")
for item, entities in items_with_entities:
    source = next(s for s in sources if s["name"] == item["raw_item"]["source_name"])
    score = calculate_score(item, entities, source["weight"])
    upsert_url_and_entities(db_path, item, entities, score, source["weight"])

# 6. View 쿼리
top_issues = get_view(db_path, "winery", limit=50)
top_wineries = get_top_entities(db_path, "winery")

# 7. 리포트 생성
sections = {
    "top_issues": top_issues,
    "winery": get_view(db_path, "winery", focus_id="winery_drc", limit=20),
    "importer": get_view(db_path, "importer", limit=20),
    "community": get_view(db_path, "community", limit=20)
}

stats = {
    "total_urls": len(raw_items),
    "top_wineries": top_wineries
}

report_path = generate_daily_report(
    target_date=date.today(),
    sections=sections,
    stats=stats,
    output_path=Path("reports/2025-01-19.html")
)

# 8. 알림 발송
pusher = TelegramPusher(bot_token="...", chat_id="...")
pusher.send_daily_summary(
    date=date.today(),
    top_items=top_issues[:5],
    stats=stats,
    report_url="https://username.github.io/WineRadar/2025-01-19.html"
)

# 9. 정리
prune_expired_urls(db_path, datetime.now())
```

---

## 요약

- **모듈화**: Collector, Analyzer, Graph, Reporter, Pusher로 명확히 분리
- **타입 안전성**: TypedDict, Protocol, Pydantic 활용
- **확장성**: MCP 서버, REST API로 확장 가능
- **테스트 용이성**: 모든 함수가 순수 함수 또는 명확한 인터페이스
