# 액티브 메타데이터 관리 시스템

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)

다양한 데이터 소스의 메타데이터를 수집, 통합, 변환 및 저장하는 시스템입니다.

이 시스템은 서로 다른 형식의 메타데이터를 표준화된 통합 카탈로그로 변환하여 조직 전체의 데이터 자산을 효율적으로 관리하고 활용할 수 있도록 지원합니다.

## 주요 기능

- 다양한 데이터 소스(공공데이터포털, 써드파티 데이터 등)로부터 메타데이터 수집
- 이기종 메타데이터 형식(DCAT/RDF, OpenSchema.org/JSON 등)의 통합 변환
- 메타데이터 품질 검증 및 보강
- 확장 가능한 메타데이터 저장소 구축
- 메타데이터 검색 및 조회 기능

## 기대 효과

- 다양한 소스의 메타데이터를 일관된 방식으로 통합 관리
- 메타데이터 수집 및 처리 자동화로 운영 효율성 증대
- 메타데이터 기반 데이터 검색성 및 활용성 향상
- 데이터 카탈로그 구축을 통한 조직 전체 데이터 자산 가시성 확보

## 시작하기

### 요구사항

- [Python](https://www.python.org/) `>=3.11`
- [uv](https://docs.astral.sh/uv/) `>= 0.5.11`
- Docker
- Docker Compose v2

### 환경 설정

#### Docker Compose로 PostgreSQL 구성

```shell
$ docker compose up -d
```

#### PostgreSQL 삭제 방법

```shell
$ docker compose down
```

#### PostgreSQL 접근 정보

- 연결 문자열: `postgresql://admin:admin@localhost:15432/datagokr`

### UV 설치 (의존성 관리 도구)

#### macOS and Linux

```bash
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows

```powershell
$ powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 의존성 설치

```bash
$ uv sync
```

## 시나리오 목록

### Raw 데이터 기반 스키마 변환 시나리오

- 원시 데이터를 통합 스키마로 변환
- `app/src/datagokr/transform.py` 의 `main` 함수 참조

### 메타데이터 기반 스키마 변환 시나리오

- 다양한 메타데이터 형식을 통합 스키마로 변환
- `app/src/datagokr/metadata_compatible.py` 의 `main` 함수 참조

### 실행 예제

```shell
# 공공데이터포털 메타데이터 처리
$ python -m app.src.datagokr.transform

# 다양한 메타데이터 소스 통합 처리
$ python -m app.src.datagokr.metadata_compatible
```

## Sample Metadata

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
