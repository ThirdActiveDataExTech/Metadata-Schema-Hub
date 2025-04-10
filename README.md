# Python FastAPI Template

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)
[![FastAPI Version](https://img.shields.io/badge/fastapi-0.115.0-yellowgreen)](https://fastapi.tiangolo.com/release-notes/#01110)
[![Loguru Version](https://img.shields.io/badge/loguru-0.7.2-orange)](https://loguru.readthedocs.io/en/stable/project/changelog.html)
[![Gunicorn Version](https://img.shields.io/badge/gunicorn-23.0.0-red)](https://gunicorn.readthedocs.io/en/stable/project/changelog.html)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pre-commit/pre-commit/main.svg)](https://results.pre-commit.ci/latest/github/pre-commit/pre-commit/main)
[![Coverage](https://gitlab.com/wisenut-research/lab/starter/python-fastapi-template/badges/main/coverage.svg?job=coverage)](https://gitlab.com/wisenut-research/lab/starter/python-fastapi-template/-/graphs/main/charts)
[![Pipeline Status](https://gitlab.com/wisenut-research/lab/starter/python-fastapi-template/badges/main/pipeline.svg)](https://gitlab.com/wisenut-research/lab/starter/python-fastapi-template/commits/main)

### Requirements

- [Python](https://www.python.org/) `>=3.11`
- [uv](https://docs.astral.sh/uv/) `>= 0.5.11`

## Quick start

![quick start guide gif](docs/docs/images/quick-start-guide.gif "quick start guide gif")

### 1. Install Requirements

### docker compose 및 psql 구성

- Docker 및 Docker Compose v2가 설치되어 있어야 함

```shell
$ docker compose up -d
```

- psql 삭제 방법
```shell
$ docker compose down
```

#### 접근 방법 

- `postgresql://admin:admin@localhost:15432/datagokr` 에 DB 접근 도구로 접근

### UV

#### macOS and Linux

```bash
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows

```powershell
$ powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Dependencies

```bash
$ uv sync
```

### pyCharm Interpreter 설정

- pyCharm이 .venv 를 인식하도록 새로 생성하고, uv 로 .venv 에 의존성 설치하는 방법

1. `/.venv/` 존재할 경우 삭제
2. [Settings] - [Project:<<YOUR_PROJECT_NAME>>] - [Python Interpreter] - [Add Interpreter]
3. Interpreter 위치 선택(default: Local Interpreter)
4. Generate New, Virtualenv 선택 후 생성
5. `uv sync` 로 의존성 설치

## Raw 데이터 기반 스키마 변환 시나리오

- `app/src/datagokr/transform.py` 의 `main` 함수 참조

## 메타데이터 기반 스키마 변환 시나리오

- `app/src/datagokr/metadata_compatible.py` 의 `main` 함수 참조

## Sample Metadata

- `sample/` 디렉토리에 sample 데이터 제공
- 공공데이터포털은 두 가지 메타데이터 제공
    - DCAT: rdf
    - openschema.org: json
- 5개의 샘플 공공데이터포털 표준데이터 메타데이터
    - https://www.data.go.kr/data/15139215/standard.do
        - dcat_15139215.rdf
        - openschema_15139215.json
    - https://www.data.go.kr/data/15107742/standard.do
        - dcat_15107742.rdf
        - openschema_15107742.json
    - https://www.data.go.kr/data/15129433/standard.do
        - dcat_15129433.rdf
        - openschema_15129433.json
    - https://www.data.go.kr/data/15139223/standard.do
        - dcat_15139223.rdf
        - openschema_15139223.json
    - https://www.data.go.kr/data/15129441/standard.do
        - dcat_15129441.rdf
        - openschema_15129441.json
- 메타데이터 추가 수집이 필요할 경우
    - `app/src/datagokr/extractor.py` 의 main 함수 참조
