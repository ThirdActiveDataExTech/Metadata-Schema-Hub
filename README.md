# Python FastAPI Template

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)

### Requirements

- [Python](https://www.python.org/) `>=3.11`
- [uv](https://docs.astral.sh/uv/) `>= 0.5.11`

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
