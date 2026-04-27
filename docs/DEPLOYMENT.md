# WineRadar 배포 & 운영 가이드

이 문서는 WineRadar를 로컬 및 GitHub Actions 환경에서 실행하고, GitHub Pages로 결과를 배포하는 절차를 정리합니다.

## 1. 사전 준비

- GitHub 계정 및 저장소 Fork
- Python 3.11 이상, Git 설치
- (선택) Telegram Bot Token & Chat ID

## 2. 로컬 실행 절차

1. 저장소 클론: `git clone https://github.com/<username>/WineRadar.git`
2. 가상환경 생성: `python -m venv venv && source venv/bin/activate`
3. 의존성 설치: `pip install -r requirements-dev.txt`
4. 환경 변수 설정 (예: `TZ=Asia/Seoul`, `WINERADAR_DB_PATH`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)
5. 개발 중에는 `pytest -m unit` 등 단계별 테스트를 먼저 실행한 뒤 `python main.py` 로 파이프라인을 점검합니다.

## 3. GitHub Actions 설정

1. Fork 저장소의 **Actions** 탭에서 워크플로를 활성화합니다.
2. **Settings → Secrets and variables → Actions** 에 필요한 비밀 값(텔레그램 토큰 등)을 등록합니다.
3. `.github/workflows/crawler.yml` 의 스케줄(`cron`)과 환경 변수를 요구 사항에 맞게 수정합니다.
4. 워크플로가 생성한 HTML 리포트를 GitHub Pages로 제공하려면 **Settings → Pages** 에서 배포 브랜치를 `gh-pages` 로 지정합니다.

## 4. GitHub Pages 동작 방식

- 워크플로는 리포트 HTML을 `report/` 혹은 별도의 아티팩트로 생성하고, `gh-pages` 브랜치에 커밋합니다.
- Pages 설정에서 Branch + 폴더(`/` 혹은 `/docs`)를 선택하면 자동으로 호스팅됩니다.
- 커스텀 도메인이 필요하면 `CNAME` 파일을 Pages 설정에 맞춰 추가하세요.

## 5. 모니터링 & 유지보수

- Actions 로그에서 Collector/Analyzer/Reporter 단계별 로그를 확인합니다.
- 실패 시 `pytest` 로 재현 가능한지 확인 후 수정합니다.
- Secrets 회전, 템플릿 수정, 소스 추가 등 설정 변경 시에는 PR로 관리하고, README/문서를 최신 상태로 유지하세요.

## 6. Troubleshooting 체크리스트

| 증상 | 원인 | 해결 |
| ---- | ---- | ---- |
| 워크플로 실패 (ImportError) | 패키지 설치 누락 | `requirements-dev.txt` 업데이트 후 재실행 |
| Pages 빈 화면 | HTML이 생성되지 않음 | Reporter 테스트(`pytest -m integration -k reporter`)로 검증 |
| 텔레그램 알림 미수신 | BOT 토큰/Chat ID 오타 | Secrets 값 재검토, `pushers` 모듈 로그 확인 |
| 타임존 오차 | 서버 타임존 기본값 사용 | `TZ` 환경 변수 설정 혹은 코드에서 `Asia/Seoul` 명시 |

## 7. 향후 자동화 아이디어

- release 브랜치 기준 배포, main 브랜치는 개발용으로 분리
- AWS S3/CloudFront 등 외부 호스팅 옵션 추가
- Grafana/Prometheus 등을 이용한 메트릭 수집

> 현재 레포는 스켈레톤 상태이므로, 실제 프로덕션 운영 시에는 보안/오류 처리/관측 가능성 등을 추가로 점검해야 합니다.
