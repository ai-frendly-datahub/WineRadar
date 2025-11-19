# WineRadar 인코딩 정책

## 개요

WineRadar 프로젝트는 **모든 텍스트 파일에 UTF-8 인코딩을 강제**합니다. 이는 다국어 지원, 크로스 플랫폼 호환성, Git 버전 관리 일관성을 위한 것입니다.

---

## UTF-8 인코딩 강제 방법

### 1. EditorConfig (.editorconfig)

모든 에디터에서 자동으로 UTF-8 인코딩을 사용하도록 설정합니다.

```ini
[*]
charset = utf-8
end_of_line = lf
```

**지원 에디터**: VSCode, IntelliJ IDEA, PyCharm, Sublime Text, Vim, Emacs 등

---

### 2. Git Attributes (.gitattributes)

Git에서 파일 인코딩과 줄바꿈을 일관되게 관리합니다.

```gitattributes
*.py text eol=lf encoding=utf-8
*.md text eol=lf encoding=utf-8
*.yaml text eol=lf encoding=utf-8
```

**효과**:
- 모든 텍스트 파일은 UTF-8로 저장
- 줄바꿈은 LF (Unix 스타일)로 통일
- Windows에서도 LF 유지

---

### 3. VSCode 설정 (.vscode/settings.json)

VSCode 사용 시 자동으로 UTF-8 인코딩을 적용합니다.

```json
{
  "files.encoding": "utf8",
  "files.autoGuessEncoding": false,
  "files.eol": "\n"
}
```

**효과**:
- 새 파일 생성 시 자동으로 UTF-8
- 인코딩 추측 비활성화 (항상 UTF-8)
- 줄바꿈 LF 강제

---

### 4. Python 파일 인코딩 선언

모든 Python 파일 첫 줄에 인코딩 선언을 추가합니다.

```python
# -*- coding: utf-8 -*-
"""모듈 독스트링"""
```

**이유**:
- Python 2 호환성 (불필요하지만 명시적)
- 코드 리뷰 시 인코딩 명확화
- 일부 도구 호환성

**Python 3.11+ 참고**: PEP 3120에 따라 기본 인코딩이 UTF-8이지만, 명시적 선언 권장

---

## 파일 타입별 인코딩 정책

### Python 파일 (.py)

```python
# -*- coding: utf-8 -*-
"""
모듈 설명
"""

def 함수이름():
    """한글 독스트링 지원"""
    pass
```

- **인코딩**: UTF-8
- **줄바꿈**: LF
- **인덴트**: 스페이스 4칸
- **최대 줄 길이**: 100

---

### YAML 파일 (.yaml, .yml)

```yaml
# UTF-8 인코딩 강제
name: "와인21"
description: "한국 와인 매체"
```

- **인코딩**: UTF-8
- **줄바꿈**: LF
- **인덴트**: 스페이스 2칸

---

### Markdown 파일 (.md)

```markdown
# 한글 제목

본문 내용...
```

- **인코딩**: UTF-8
- **줄바꿈**: LF
- **후행 공백**: 유지 (Markdown 줄바꿈 용)

---

### JSON 파일 (.json)

```json
{
  "name": "와인라더",
  "description": "한글 지원"
}
```

- **인코딩**: UTF-8
- **줄바꿈**: LF
- **인덴트**: 스페이스 2칸

---

### HTML/Jinja2 템플릿 (.html, .jinja, .jinja2)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>와인라더</title>
</head>
```

- **인코딩**: UTF-8
- **줄바꿈**: LF
- **인덴트**: 스페이스 2칸
- **HTML meta 태그**: `<meta charset="UTF-8">` 필수

---

### 텍스트 파일 (.txt)

```
와인
wine
샴페인
```

- **인코딩**: UTF-8
- **줄바꿈**: LF

---

## 인코딩 문제 해결

### 문제 1: 한글이 깨져서 보임

**증상**: `와인` → `���`

**원인**: 파일이 UTF-8이 아닌 다른 인코딩(CP949, EUC-KR 등)으로 저장됨

**해결**:

1. VSCode에서 파일 열기
2. 우측 하단 인코딩 클릭 (예: "EUC-KR")
3. "Reopen with Encoding" → "UTF-8" 선택
4. 파일 내용 확인
5. "Save with Encoding" → "UTF-8" 선택

또는 명령 팔레트 (Ctrl+Shift+P):
```
> Change File Encoding
> Save with Encoding: UTF-8
```

---

### 문제 2: Git diff에서 한글이 깨짐

**증상**: Git diff 결과에서 한글이 `\xec\x99\x80` 같이 표시됨

**원인**: Git이 파일을 바이너리로 인식

**해결**:

`.gitattributes` 확인:
```gitattributes
*.py text eol=lf encoding=utf-8
```

Git 설정:
```bash
git config --global core.quotepath false
git config --global gui.encoding utf-8
git config --global i18n.commitencoding utf-8
git config --global i18n.logoutputencoding utf-8
```

---

### 문제 3: Windows에서 파일 저장 시 BOM 추가됨

**증상**: 파일 시작 부분에 `\xef\xbb\xbf` (BOM) 추가

**원인**: 일부 에디터가 UTF-8 BOM으로 저장

**해결**:

VSCode 설정:
```json
{
  "files.encoding": "utf8"  // UTF-8 without BOM
}
```

기존 파일 BOM 제거:
```bash
# PowerShell
$fileContent = Get-Content -Path "file.py" -Encoding UTF8
[System.IO.File]::WriteAllText("file.py", $fileContent)

# Linux/Mac
sed -i '1s/^\xEF\xBB\xBF//' file.py
```

---

### 문제 4: Python에서 한글 출력 시 에러

**증상**: `UnicodeEncodeError: 'cp949' codec can't encode character`

**원인**: Windows 콘솔이 CP949 인코딩 사용

**해결**:

1. 환경변수 설정:
```bash
# Windows PowerShell
$env:PYTHONIOENCODING = "utf-8"

# Linux/Mac
export PYTHONIOENCODING=utf-8
```

2. Python 코드에서 명시:
```python
import sys
import io

# stdout을 UTF-8로 강제
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

3. GitHub Actions에서:
```yaml
env:
  PYTHONIOENCODING: utf-8
  LANG: en_US.UTF-8
```

---

## 검증 방법

### 파일 인코딩 확인

**Linux/Mac**:
```bash
file -i filename.py
# 결과: filename.py: text/x-python; charset=utf-8
```

**Python**:
```python
import chardet

with open('filename.py', 'rb') as f:
    result = chardet.detect(f.read())
    print(result['encoding'])  # utf-8
```

---

### 프로젝트 전체 인코딩 검사

```bash
# 모든 Python 파일 인코딩 확인
find . -name "*.py" -exec file -i {} \; | grep -v utf-8

# UTF-8이 아닌 파일 찾기
find . -type f -name "*.py" -o -name "*.md" | while read f; do
  if ! file -i "$f" | grep -q utf-8; then
    echo "$f: NOT UTF-8"
  fi
done
```

---

### 인코딩 선언 확인

```bash
# Python 파일에 인코딩 선언이 있는지 확인
grep -L "coding: utf-8" **/*.py
```

---

## 모범 사례

### ✅ 권장사항

1. **항상 UTF-8 사용**
   - 모든 텍스트 파일은 UTF-8
   - BOM 없이 저장

2. **에디터 설정**
   - VSCode/PyCharm 등에서 기본 인코딩을 UTF-8로 설정
   - EditorConfig 플러그인 설치

3. **Git 설정**
   - `.gitattributes` 활용
   - `core.quotepath false` 설정

4. **Python 파일**
   - `# -*- coding: utf-8 -*-` 선언 추가
   - 한글 주석/독스트링 자유롭게 사용

5. **HTML 파일**
   - `<meta charset="UTF-8">` 필수
   - HTTP 헤더도 UTF-8 명시

---

### ❌ 피해야 할 사항

1. **CP949, EUC-KR 사용 금지**
   - Windows 기본 인코딩이지만 사용하지 말 것
   - 크로스 플랫폼 호환성 문제

2. **인코딩 혼용 금지**
   - 한 프로젝트에 여러 인코딩 섞지 말 것
   - UTF-8로 통일

3. **BOM 사용 금지**
   - UTF-8 BOM은 일부 도구에서 문제 발생
   - UTF-8 without BOM 사용

4. **인코딩 추측 금지**
   - `chardet` 같은 추측 도구 의존 지양
   - 명시적으로 UTF-8 선언

---

## CI/CD에서의 인코딩 검증

### GitHub Actions 워크플로우

```yaml
name: Encoding Check

on: [push, pull_request]

jobs:
  check-encoding:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check UTF-8 encoding
        run: |
          # Python 파일 인코딩 검사
          find . -name "*.py" | while read file; do
            if ! file -i "$file" | grep -q "utf-8"; then
              echo "ERROR: $file is not UTF-8"
              exit 1
            fi
          done

      - name: Check encoding declaration
        run: |
          # Python 파일에 인코딩 선언 확인
          missing=$(find . -name "*.py" -type f -exec grep -L "coding: utf-8" {} \;)
          if [ -n "$missing" ]; then
            echo "ERROR: Missing encoding declaration:"
            echo "$missing"
            exit 1
          fi
```

---

## 요약

| 항목 | 정책 |
|------|------|
| **인코딩** | UTF-8 (without BOM) |
| **줄바꿈** | LF (Unix 스타일) |
| **Python 인코딩 선언** | `# -*- coding: utf-8 -*-` (필수) |
| **HTML meta 태그** | `<meta charset="UTF-8">` (필수) |
| **에디터 설정** | .editorconfig, .vscode/settings.json |
| **Git 설정** | .gitattributes |

---

## 참고 자료

- [PEP 263 - Defining Python Source Code Encodings](https://www.python.org/dev/peps/pep-0263/)
- [PEP 3120 - Using UTF-8 as the default source encoding](https://www.python.org/dev/peps/pep-3120/)
- [EditorConfig](https://editorconfig.org/)
- [Git Attributes](https://git-scm.com/docs/gitattributes)
- [Unicode HOWTO](https://docs.python.org/3/howto/unicode.html)
