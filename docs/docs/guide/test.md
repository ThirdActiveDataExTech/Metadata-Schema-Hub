# Python FastAPI Template 린트 및 테스트 가이드

Python FastAPI Template은 코드 품질 관리와 테스트를 위해 다음 도구들을 사용합니다:

- `ruff`: 코드 린터
- `pyright`: 정적 타입 체커
- `pytest`: 테스트 실행기

이 가이드는 이러한 도구들의 사용법과 버전 호환성 설정 방법을 설명합니다.

---

## 의존성 설치

린트 및 테스트에 필요한 의존성을 설치하려면 다음 명령어를 실행하세요:

```shell
uv sync --group lint --group test
```

모든 의존성 그룹을 설치하려면:

```shell
uv sync --all-groups
```

---

## 사용 방법

### ruff

```shell
ruff check .
```

### pyright

```shell
pyright ./
```

### pytest

```shell
pytest
```

---

## 버전 호환성 설정

기본적으로 Python 3.9부터 3.12까지 모든 버전을 테스트합니다.

특정 버전만 테스트하려면 (예: Python 3.12) `.gitlab-ci.yaml`을 다음과 같이 설정하세요:

```yaml
ruff-lint:
  parallel:
    matrix:
      - PYTHON_VERSION: [ "py312" ]
pyright-lint:
  parallel:
    matrix:
      - PYTHON_VERSION: [ "3.12" ]
pytest:
  parallel:
    matrix:
      - PYTHON_VERSION: [ "3.12" ]
```

## 린트 및 테스트 도구 추가 설정

본 프로젝트는 `pyproject.toml` 파일에서 `ruff`와 `pyright`에 대한 설정을 관리합니다.

### ruff 설정

`ruff`에 대한 설정은 `[tool.ruff]` 섹션에서 확인할 수 있습니다.

### pyright 설정

pyright 설정은 `[tool.pyright]` 섹션에 정의되어 있습니다.