# 시나리오 목록

## 요구사항

- [Python](https://www.python.org/) `>=3.11`
- [uv](https://docs.astral.sh/uv/) `>= 0.5.11`
- Docker
- Docker Compose v2

## 환경 설정

### Docker Compose로 PostgreSQL 구성

```shell
$ docker compose up -d
```

### PostgreSQL 삭제 방법

```shell
$ docker compose down
```

### PostgreSQL 접근 정보

- 연결 문자열: `postgresql://admin:admin@localhost:15432/datagokr`

## UV 설치 (의존성 관리 도구)

### macOS and Linux

```bash
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

```powershell
$ powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 의존성 설치 및 등록

```bash
$ uv sync
$ export PYTHONPATH=$(pwd)
```

## Raw 데이터 기반 스키마 변환 시나리오

- 원시 데이터를 통합 스키마로 변환
- `uv run app/src/datagokr/transform.py`
- 해당 파일의 `main` 함수 참조

## 메타데이터 기반 스키마 변환 시나리오

- 다양한 메타데이터 형식을 통합 스키마로 변환
- `uv run app/src/datagokr/metadata_compatible.py`
- 해당 파일의 `main` 함수 참조

## 실행 예제

```shell
# 공공데이터포털 메타데이터 처리
$ python -m app.src.datagokr.transform

# 다양한 메타데이터 소스 통합 처리
$ python -m app.src.datagokr.metadata_compatible
```

# Sample Metadata

- `sample/` 디렉토리에 sample 데이터 제공
- 공공데이터포털 메타데이터 형식:
    - DCAT (RDF 형식)
    - OpenSchema.org (JSON 형식)
- 샘플 데이터셋 목록:
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
- 메타데이터 추가 수집이 필요할 경우 `app/src/datagokr/extractor.py` 의 main 함수 참조
