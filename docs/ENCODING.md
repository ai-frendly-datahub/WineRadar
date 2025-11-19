# Encoding 정책

- 모든 소스 코드는 UTF-8 (BOM 없음) 으로 저장합니다.
- Windows 환경에서도 `git config core.autocrlf false` 를 권장하고, `.gitattributes` 로 `*.py text eol=lf` 를 강제합니다.
- 문서 역시 UTF-8을 사용하며, 한글이 포함된 경우 PR에서 미리보기(Syntax highlighting)를 확인합니다.
- 터미널 출력은 가능하면 ASCII/영문 로그를 사용하고, 사용자 메시지는 한국어로 별도 노출합니다.
- 외부에서 받은 TSV/CSV 파일을 사용할 경우 `scripts/encoding_check.py` (추가 예정)로 변환 상태를 검증합니다.

> 인코딩 오류를 발견하면 원본을 재작성하기보다는 문제 파일 전체를 올바른 인코딩으로 다시 저장하세요.
