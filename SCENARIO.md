# 시나리오 목록

## 요구사항

- [Python](https://www.python.org/) `>=3.11`
- [uv](https://docs.astral.sh/uv/) `>= 0.5.11`
- Docker
- Docker Compose v2

## 환경 설정

### 카탈로그 실행 방법

```shell
$ docker compose build  # 최초 1회만 수행하여 이미지 빌드
$ docker compose up -d
```

### 카탈로그 삭제 방법

```shell
$ docker compose down
```

### PostgreSQL 접근 정보

- Database URL: `postgresql://<username>:<password>@localhost:5432/datagokr`
- 기본 자격증명: username=`admin`, password=`admin` (개발 환경용)

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

* 원하는 port 로 변경 가능

## API 기반 메타데이터 처리 시나리오

* **해당 API 는 http://localhost:{port}/docs 에 Swagger UI 를 통해 제공**

* **Swagger UI 상단의 Authorize 항목에 `x-token` 값을 입력해 사용 가능**

* `x-token` 기본값은 `wisenut` 입니다.

### 메타데이터 변환 API

#### Schema.org JSON 메타데이터 변환
```bash
# Schema.org JSON-LD 파일 변환
curl -X POST "http://localhost:{port}/metadata/convert/schema-org" \
  -H 'x-token: {x-token}' \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample/schema_org_15139215.json"
```

#### DCAT RDF 메타데이터 변환
```bash
# DCAT RDF/XML 파일 변환
curl -X POST "http://localhost:{port}/metadata/convert/dcat" \
  -H 'x-token: {x-token}' \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample/dcat_15139215.rdf"
```

### 카탈로그 엔트리 관리 API

#### 메타데이터 파일 임포트
```bash
# JSON 메타데이터 파일 임포트 및 카탈로그 엔트리 생성
curl -X POST "http://localhost:{port}/catalog/import" \
  -H 'x-token: {x-token}' \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample/schema_org_15139215.json"

# DCAT RDF 파일 임포트
curl -X POST "http://localhost:{port}/catalog/import" \
  -H 'x-token: {x-token}' \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample/dcat_15139215.rdf"
```

#### 카탈로그 엔트리 조회
```bash
# 전체 카탈로그 목록 조회
curl "http://localhost:{port}/catalog/entries?limit=10" \
  -H 'x-token: {x-token}'

# 특정 카탈로그 엔트리 조회
curl "http://localhost:{port}/catalog/entries/31" \
  -H 'x-token: {x-token}'

# 특정 카탈로그 엔트리의 원본 메타데이터 조회 (JSON 형식)
curl "http://localhost:{port}/catalog/entries/raw-metadata/31?output_format=json" \
  -H 'x-token: {x-token}'

# 특정 카탈로그 엔트리의 원본 메타데이터 조회 (XML 형식)
curl "http://localhost:{port}/catalog/entries/raw-metadata/31?output_format=xml" \
  -H 'x-token: {x-token}'

# 텍스트 검색
curl "http://localhost:{port}/catalog/entries?query=교통&limit=20" \
  -H 'x-token: {x-token}'

# 키워드 필터링
curl "http://localhost:{port}/catalog/entries?keyword=dataset&limit=20" \
  -H 'x-token: {x-token}'
```

#### 카탈로그 CSV 내보내기
```bash
# CSV 형식으로 내보내기
curl "http://localhost:{port}/catalog/export/csv?limit=100" \
  -H 'x-token: {x-token}' \
  -o catalog_entries.csv
```

### 컬럼 관계 관리 API

#### 컬럼 관계 생성
```bash
# 카탈로그와 메타데이터 컬럼 간 관계 생성
curl -X POST "http://localhost:{port}/relation/" \
  -H 'x-token: {x-token}' \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_column": "title",
    "metadata_column": "dc:title",
    "correlation": 0.95
  }'
```

#### 컬럼 관계 조회
```bash
# 카탈로그 컬럼으로 관계 조회
curl "http://localhost:{port}/relation/catalog-column?catalog_column=title" \
  -H 'x-token: {x-token}'

# 메타데이터 컬럼으로 관계 조회
curl "http://localhost:{port}/relation/metadata-column?metadata_column=dc:title" \
  -H 'x-token: {x-token}'
```

#### 메타데이터 엔트리 조회
```bash
# 전체 메타데이터 목록 조회
curl "http://localhost:{port}/metadata/entries?limit=10" \
  -H 'x-token: {x-token}'

# 텍스트 검색 (값, 스키마에서 검색)
curl "http://localhost:{port}/metadata/entries?query=title&limit=20" \
  -H 'x-token: {x-token}'

# 메타데이터 스키마로 필터링
curl "http://localhost:{port}/metadata/entries?schema=dc:title&limit=20" \
  -H 'x-token: {x-token}'

# 메타데이터 ID로 필터링
curl "http://localhost:{port}/metadata/entries?metadata_id=18e6f7bc-5791-488a-bc7b-d78b18e51dcd&limit=20" \
  -H 'x-token: {x-token}'

# 복합 검색 (텍스트 + 스키마)
curl "http://localhost:{port}/metadata/entries?query=교통&schema=dc:title&limit=20" \
  -H 'x-token: {x-token}'

# UUID로 특정 메타데이터 엔트리 조회
curl "http://localhost:{port}/metadata/18e6f7bc-5791-488a-bc7b-d78b18e51dcd" \
  -H 'x-token: {x-token}'
```

# Sample Metadata

- `sample/` 디렉토리에 sample 데이터 제공
- 공공데이터포털 메타데이터 형식:
    - DCAT (RDF 형식)
    - schema.org (JSON 형식)
- 샘플 데이터셋 목록:
    - https://www.data.go.kr/data/15139215/standard.do
        - dcat_15139215.rdf
        - schema_org_15139215.json
    - https://www.data.go.kr/data/15107742/standard.do
        - dcat_15107742.rdf
        - schema_org_15107742.json
    - https://www.data.go.kr/data/15129433/standard.do
        - dcat_15129433.rdf
        - schema_org_15129433.json
    - https://www.data.go.kr/data/15139223/standard.do
        - dcat_15139223.rdf
        - schema_org_15139223.json
    - https://www.data.go.kr/data/15129441/standard.do
        - dcat_15129441.rdf
        - schema_org_15129441.json
