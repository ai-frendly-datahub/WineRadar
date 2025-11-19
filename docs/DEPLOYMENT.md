# WineRadar 배포 및 운영 가이드

## 개요

WineRadar는 GitHub Actions를 통해 자동으로 실행되며, GitHub Pages로 리포트를 배포하는 서버리스 아키텍처입니다.

---

## 1. 사전 요구사항

### 1.1 필수 항목

- GitHub 계정 및 리포지토리
- Python 3.11 이상
- Git 설치
- (선택) Telegram Bot (알림용)

### 1.2 권장 사항

- VSCode 또는 PyCharm (로컬 개발)
- SQLite 브라우저 (DB 확인용)

---

## 2. 로컬 개발 환경 설정

### 2.1 리포지토리 클론

```bash
git clone https://github.com/<username>/WineRadar.git
cd WineRadar
```

---

### 2.2 Python 가상환경 생성

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

---

### 2.3 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt** (업데이트 필요):
```
requests>=2.31.0
beautifulsoup4>=4.12.0
pyyaml>=6.0
jinja2>=3.1.0
feedparser>=6.0.0
python-dateutil>=2.8.0
pydantic>=2.0.0

# 개발 도구
pytest>=7.4.0
mypy>=1.5.0
black>=23.0.0
ruff>=0.1.0
```

설치:
```bash
pip install -r requirements.txt
```

---

### 2.4 코드 품질 도구 설정

#### mypy 설정 (mypy.ini)

```ini
[mypy]
python_version = 3.11
strict = True
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

[mypy-feedparser.*]
ignore_missing_imports = True

[mypy-bs4.*]
ignore_missing_imports = True
```

#### black 설정 (pyproject.toml)

```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
```

#### ruff 설정 (pyproject.toml)

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "N"]
ignore = ["E501"]
```

파일 생성:
```bash
# mypy.ini 생성 (위 내용 복사)
# pyproject.toml 생성 (위 내용 복사)
```

실행:
```bash
# 타입 체크
mypy .

# 코드 포맷팅
black .

# 린팅
ruff check .
```

---

### 2.5 로컬 실행 테스트

```bash
# 데이터베이스 초기화
python -c "from graph.graph_store import init_database; from pathlib import Path; init_database(Path('wineradar.db'))"

# 메인 파이프라인 실행
python main.py
```

---

## 3. GitHub 배포 설정

### 3.1 리포지토리 설정

#### 1) GitHub Pages 활성화

1. GitHub 리포지토리 → Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: **gh-pages** / (root)
4. Save

#### 2) Actions 권한 설정

1. Settings → Actions → General
2. Workflow permissions: **Read and write permissions**
3. Allow GitHub Actions to create and approve pull requests: ✅ 체크
4. Save

---

### 3.2 GitHub Secrets 설정 (선택적)

Telegram 알림을 사용하는 경우:

1. GitHub 리포지토리 → Settings → Secrets and variables → Actions
2. **New repository secret** 클릭
3. 다음 시크릿 추가:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token (BotFather로 생성) |
| `TELEGRAM_CHAT_ID` | Chat ID (Bot에게 메시지 보낸 후 API로 확인) |

**Telegram Bot 생성 방법**:

```bash
# 1. Telegram에서 @BotFather 검색
# 2. /newbot 명령어로 봇 생성
# 3. 봇 토큰 복사 (예: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)

# 4. Chat ID 확인
# - 봇에게 아무 메시지 보내기
# - 브라우저에서 https://api.telegram.org/bot<TOKEN>/getUpdates 접속
# - "chat":{"id":123456789} 에서 ID 복사
```

---

### 3.3 소스 URL 설정

[config/sources.yaml](../config/sources.yaml)의 예시 URL을 실제 RSS 피드로 교체:

```yaml
sources:
  - name: "Wine21"
    id: "media_wine21"
    type: "media"
    country: "KR"
    enabled: true
    weight: 2.8
    config:
      list_url: "https://www.wine21.com/rss"  # 실제 URL로 변경

  - name: "Decanter"
    id: "media_decanter"
    type: "media"
    country: "GLOBAL"
    enabled: true
    weight: 3.0
    config:
      list_url: "https://www.decanter.com/feed/"  # 실제 URL로 변경
```

---

### 3.4 워크플로우 수정

[.github/workflows/crawler.yml](.github/workflows/crawler.yml) 업데이트:

```yaml
name: WineRadar Crawler

on:
  workflow_dispatch:  # 수동 실행
  schedule:
    - cron: "0 0 * * *"  # 매일 00:00 UTC (한국 09:00)

jobs:
  crawl-and-report:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run WineRadar
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python main.py

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        if: success()
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./reports
          publish_branch: gh-pages
          keep_files: true  # 이전 리포트 유지
```

---

## 4. 배포 프로세스

### 4.1 초기 배포

```bash
# 1. 로컬에서 최종 테스트
python main.py

# 2. Git 커밋 및 푸시
git add .
git commit -m "Setup WineRadar for production"
git push origin main

# 3. GitHub Actions에서 수동 실행
# - GitHub 리포지토리 → Actions → WineRadar Crawler
# - Run workflow 클릭
# - Run workflow 버튼 클릭
```

---

### 4.2 자동 실행 확인

- 매일 00:00 UTC (한국 시간 오전 9시)에 자동 실행
- Actions 탭에서 실행 로그 확인
- 실패 시 이메일 알림 (GitHub 설정에 따라)

---

### 4.3 리포트 확인

배포 완료 후:
- URL: `https://<username>.github.io/WineRadar/`
- 최신 리포트: `https://<username>.github.io/WineRadar/YYYY-MM-DD.html`

---

## 5. 운영 및 모니터링

### 5.1 로그 확인

#### GitHub Actions 로그

1. 리포지토리 → Actions
2. 최근 워크플로우 실행 클릭
3. 각 스텝별 로그 확인

#### 로컬 로그

```bash
# logs/ 디렉토리 확인
ls logs/

# 최신 로그 보기
tail -f logs/wineradar_YYYY-MM-DD.log
```

---

### 5.2 데이터베이스 확인

```bash
# SQLite CLI
sqlite3 wineradar.db

# 노드 수 확인
SELECT type, COUNT(*) FROM nodes GROUP BY type;

# 최근 URL 확인
SELECT name, json_extract(meta_json, '$.published_at')
FROM nodes
WHERE type = 'url'
ORDER BY updated_at DESC
LIMIT 10;

# 종료
.exit
```

또는 [DB Browser for SQLite](https://sqlitebrowser.org/) 사용

---

### 5.3 주요 지표 모니터링

**일일 체크 사항**:
- [ ] GitHub Actions 실행 성공 여부
- [ ] 수집된 URL 수 (최소 50개 이상 권장)
- [ ] 리포트 페이지 정상 렌더링
- [ ] Telegram 알림 수신 (설정한 경우)

**주간 체크 사항**:
- [ ] 데이터베이스 크기 (<100MB 권장)
- [ ] 엔티티 추출 정확도 (샘플링)
- [ ] 소스별 수집 실패율 (<10% 권장)

**월간 체크 사항**:
- [ ] 스냅샷 파일 정리 (30일 이상 삭제)
- [ ] 엔티티 사전 업데이트 (새 와이너리/수입사 추가)
- [ ] GitHub Actions 사용량 (무료 플랜 2,000분/월 제한)

---

### 5.4 알림 설정

#### 실패 알림 (GitHub Actions)

워크플로우에 알림 스텝 추가:

```yaml
- name: Notify on failure
  if: failure()
  run: |
    curl -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage" \
      -d "chat_id=${{ secrets.TELEGRAM_CHAT_ID }}" \
      -d "text=⚠️ WineRadar 파이프라인 실패: ${{ github.run_id }}"
```

---

## 6. 트러블슈팅

### 6.1 일반적인 문제

#### 문제 1: GitHub Actions 실행 실패

**증상**: Actions 탭에서 빨간색 ❌ 표시

**해결 방법**:
1. 로그 확인 (Actions → 실패한 워크플로우 클릭)
2. 에러 메시지 확인
3. 일반적인 원인:
   - 의존성 설치 실패 → requirements.txt 확인
   - 코드 에러 → 로컬에서 `python main.py` 테스트
   - Secrets 누락 → Settings → Secrets 확인

---

#### 문제 2: RSS 피드 파싱 실패

**증상**: 수집된 URL 수가 0 또는 매우 적음

**해결 방법**:
1. RSS URL이 유효한지 확인
   ```bash
   curl -I https://www.wine21.com/rss
   ```
2. feedparser 테스트
   ```python
   import feedparser
   feed = feedparser.parse("https://www.wine21.com/rss")
   print(len(feed.entries))
   ```
3. 소스가 막혔는지 확인 (User-Agent 설정 필요할 수 있음)

---

#### 문제 3: GitHub Pages 배포 안 됨

**증상**: `https://<username>.github.io/WineRadar/` 접속 시 404

**해결 방법**:
1. Settings → Pages에서 Source가 gh-pages 브랜치인지 확인
2. gh-pages 브랜치가 존재하는지 확인
   ```bash
   git branch -r
   ```
3. Actions 탭에서 "pages build and deployment" 성공 확인
4. 최대 5분 소요될 수 있음 (대기 후 재확인)

---

#### 문제 4: 데이터베이스 락

**증상**: `database is locked` 에러

**해결 방법**:
1. SQLite는 동시 쓰기 지원 안 함
2. 워크플로우가 중복 실행되지 않도록 설정
   ```yaml
   concurrency:
     group: wineradar-pipeline
     cancel-in-progress: false
   ```

---

#### 문제 5: GitHub Actions 시간 초과

**증상**: 워크플로우가 6시간 후 자동 종료

**해결 방법**:
1. 수집 소스 수 줄이기
2. 병렬 처리 도입
3. 타임아웃 설정
   ```yaml
   - name: Run WineRadar
     timeout-minutes: 10
     run: python main.py
   ```

---

### 6.2 성능 최적화

#### 데이터베이스 최적화

```sql
-- 인덱스 확인
SELECT name FROM sqlite_master WHERE type='index';

-- VACUUM으로 공간 회수
VACUUM;

-- ANALYZE로 쿼리 최적화
ANALYZE;
```

#### Collector 병렬화

```python
from concurrent.futures import ThreadPoolExecutor

def collect_parallel(collectors: list[Collector]) -> list[RawItem]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(c.collect) for c in collectors]
        results = [f.result() for f in futures]
    return [item for result in results for item in result]
```

---

## 7. 백업 및 복구

### 7.1 데이터베이스 백업

```bash
# 로컬 백업
cp wineradar.db backups/wineradar_$(date +%Y%m%d).db

# GitHub Actions에서 자동 백업
- name: Backup Database
  run: |
    mkdir -p backups
    cp wineradar.db backups/wineradar_$(date +%Y%m%d).db

- name: Upload Backup
  uses: actions/upload-artifact@v3
  with:
    name: database-backup
    path: backups/
    retention-days: 30
```

---

### 7.2 복구

```bash
# 백업에서 복원
cp backups/wineradar_20250119.db wineradar.db

# 데이터베이스 재구축 (최악의 경우)
rm wineradar.db
python -c "from graph.graph_store import init_database; from pathlib import Path; init_database(Path('wineradar.db'))"
python main.py  # 새로 수집
```

---

## 8. 스케일링 고려사항

### 8.1 데이터 증가 시

**현재 구조 한계**:
- SQLite 파일 크기: 최대 140TB (실질적으로 ~100GB 권장)
- GitHub Pages: 1GB 제한
- GitHub Actions: 무료 플랜 2,000분/월

**대응 방안**:

1. **단기** (MVP 단계, ~1년):
   - TTL 단축 (30일 → 14일)
   - 리포트 아카이빙 (월간 요약만 유지)
   - pruning 주기 증가 (매일 → 매주)

2. **중기** (사용자 증가 시):
   - PostgreSQL로 마이그레이션
   - AWS S3 + CloudFront로 리포트 배포
   - GitHub Actions → AWS Lambda

3. **장기** (본격 서비스):
   - 그래프 DB (Neo4j, ArangoDB)
   - 전용 웹 서버
   - 실시간 업데이트

---

### 8.2 소스 증가 시

**현재**: 5-10개 소스
**확장**: 50개 이상 소스

**대응**:
- Collector 우선순위 설정
- 소스별 실행 주기 조정 (중요 소스 = 매일, 기타 = 주간)
- Rate limiting 강화

---

## 9. 보안 고려사항

### 9.1 Secrets 관리

- **절대 Git에 커밋하지 말 것**:
  - API 키, 토큰
  - 비밀번호
  - 개인정보

- GitHub Secrets 사용
- 환경변수로만 접근

---

### 9.2 의존성 보안

```bash
# 의존성 취약점 스캔
pip install safety
safety check

# GitHub Dependabot 활성화
# Settings → Security → Dependabot alerts: ✅
```

---

### 9.3 Rate Limiting

```python
import time

class RateLimitedCollector:
    def __init__(self, requests_per_minute: int = 10):
        self.delay = 60.0 / requests_per_minute

    def collect(self):
        for item in self._fetch_items():
            yield item
            time.sleep(self.delay)
```

---

## 10. 체크리스트

### 10.1 배포 전 체크리스트

- [ ] 로컬에서 `python main.py` 성공
- [ ] 테스트 통과 (`pytest`)
- [ ] 타입 체크 통과 (`mypy`)
- [ ] 린팅 통과 (`ruff`, `black`)
- [ ] [config/sources.yaml](../config/sources.yaml) 실제 URL로 변경
- [ ] GitHub Secrets 설정 (Telegram 사용 시)
- [ ] GitHub Pages 활성화
- [ ] Actions 권한 설정 (Read and write)

---

### 10.2 배포 후 체크리스트

- [ ] GitHub Actions 첫 실행 성공
- [ ] `https://<username>.github.io/WineRadar/` 접속 확인
- [ ] 리포트에 데이터 표시 확인
- [ ] Telegram 알림 수신 (설정 시)
- [ ] 데이터베이스에 노드/엣지 저장 확인

---

### 10.3 주간 점검 체크리스트

- [ ] 지난 7일간 Actions 실행 성공률 >90%
- [ ] 일평균 수집 URL 수 >50
- [ ] 데이터베이스 크기 <100MB
- [ ] 엔티티 추출 샘플 확인 (정확도 체크)
- [ ] 리포트 페이지 로딩 속도 <2초

---

## 11. 참고 자료

### 11.1 공식 문서

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [GitHub Pages 문서](https://docs.github.com/en/pages)
- [feedparser 문서](https://feedparser.readthedocs.io/)
- [SQLite 문서](https://www.sqlite.org/docs.html)
- [Jinja2 문서](https://jinja.palletsprojects.com/)

---

### 11.2 유용한 도구

- [DB Browser for SQLite](https://sqlitebrowser.org/): SQLite GUI
- [Postman](https://www.postman.com/): API 테스트
- [RSS Feed Validator](https://validator.w3.org/feed/): RSS 피드 검증
- [Telegram Bot API](https://core.telegram.org/bots/api): 봇 문서

---

### 11.3 커뮤니티

- [GitHub Discussions](https://github.com/<username>/WineRadar/discussions): Q&A
- [Issues](https://github.com/<username>/WineRadar/issues): 버그 리포트

---

## 부록: 환경변수 목록

| 변수명 | 필수 | 기본값 | 설명 |
|--------|------|--------|------|
| `TELEGRAM_BOT_TOKEN` | No | - | Telegram 봇 토큰 |
| `TELEGRAM_CHAT_ID` | No | - | Telegram 채팅 ID |
| `WINERADAR_DB_PATH` | No | `wineradar.db` | SQLite DB 경로 |
| `WINERADAR_CONFIG_PATH` | No | `config/config.yaml` | 설정 파일 경로 |
| `WINERADAR_LOG_LEVEL` | No | `INFO` | 로그 레벨 (DEBUG/INFO/WARNING/ERROR) |

---

## 요약

1. **로컬 개발**: Python 3.11, venv, 의존성 설치
2. **GitHub 설정**: Pages 활성화, Secrets 추가, 소스 URL 변경
3. **배포**: Git push → GitHub Actions 자동 실행 → Pages 배포
4. **모니터링**: Actions 로그, DB 확인, 주간 점검
5. **운영**: 백업, 보안, 성능 최적화

**첫 배포 시작**: `python main.py` 로컬 테스트 → Git push → Actions 실행 확인
