# 시나리오 목록

## 요구사항

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

- Database URL: `postgresql://{username}:{password}@localhost:5432/datagokr`
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

## 서비스 구성

| 서비스 | 포트 | Swagger UI | 설명 |
| ------ | ---- | ---------- | ---- |
| metadata-ingestion | 8085 | `http://localhost:{port}/docs` | 메타데이터 수집/워크플로우 |
| catalog-service | 8084 | `http://localhost:{port}/docs` | 카탈로그 조회/리니지 |

- `x-token` 기본값은 `wisenut` 입니다.
- 아래 예시의 `{port}`, `{x-token}`은 실제 값으로 대체하세요.

---

## 메타데이터 수집 워크플로우


### 워크플로우 흐름

```
[메타데이터 파일 업로드] → [드래프트 생성] → [드래프트 검토 및 카탈로그 발행]
```

### 상태 흐름

**수집 실행 상태 (IngestionRun)**:

```
STORED → DRAFTED
       ↘ FAILED
```

**드래프트 상태 (Draft)**:

```
PENDING → PUBLISHED
        ↘ DISCARDED
```

---

## API 기반 메타데이터 처리 시나리오

### 1. Store Phase: 메타데이터 저장

> **Service**: `metadata-ingestion` (port 8085)

파일 업로드 후 스냅샷 생성 및 메타데이터 파싱

```bash
curl -X POST "http://localhost:{port}/ingestion/store" \
  -H "x-token: {x-token}" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample/schema_org_15139215.json"
```

**Response**:

```json
{
  "code": 102200,
  "message": "API Response Success",
  "result": {
    "snapshot_id": "a1b2c3d4e5f6...",
    "run_id": "18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
    "metadata_count": 15,
    "state": "STORED"
  },
  "description": "Store Phase 완료: 메타데이터 15건 저장"
}
```

- 지원 형식: `.json`, `.jsonld`, `.xml`, `.rdf`

---

### 2. Draft Phase: 드래프트 생성

> **Service**: `metadata-ingestion` (port 8085)

Store 완료 후 카탈로그 드래프트 생성 (자동 매핑 적용)

```bash
curl -X POST "http://localhost:{port}/ingestion/draft/{run_id}" \
  -H "x-token: {x-token}"
```

**Response**:

```json
{
  "code": 102200,
  "message": "API Response Success",
  "result": {
    "draft": {
      "id": 1,
      "snapshot_id": "a1b2c3d4e5f6...",
      "mapping_version": "v1.0",
      "status": "PENDING",
      "title": "교통 데이터",
      "description": "서울시 교통 데이터",
      "publisher": "서울시",
      "keyword": ["교통", "데이터"],
      "mapping_evidence": {
        "title": {
          "candidates": [
            {"metadata_column": "dct:title", "correlation": 0.95, "value": "교통 데이터"},
            {"metadata_column": "schema:name", "correlation": 0.82, "value": "교통 데이터셋"}
          ],
          "recommended": {"metadata_column": "dct:title", "correlation": 0.95, "value": "교통 데이터"},
          "decided": {"metadata_column": "dct:title", "correlation": 0.95, "value": "교통 데이터", "out_of_candidates": false}
        }
      }
    },
    "mapping_version": "v1.0",
    "state": "DRAFTED"
  },
  "description": "Draft Phase 완료: 드래프트 1 생성"
}
```

---

### 3. 드래프트 검토/수정 (선택)

> **Service**: `metadata-ingestion` (port 8085)

#### 드래프트 조회

```bash
curl "http://localhost:{port}/draft/entries/{draft_id}" \
  -H "x-token: {x-token}"
```

#### 매핑 증거(Evidence) 조회

```bash
curl "http://localhost:{port}/draft/entries/{draft_id}/evidence" \
  -H "x-token: {x-token}"
```

#### 메타데이터 옵션 조회

드래프트 편집 시 선택 가능한 메타데이터 목록

```bash
curl "http://localhost:{port}/draft/entries/{draft_id}/metadata-options" \
  -H "x-token: {x-token}"
```

#### 필드 수정

```bash
curl -X PATCH "http://localhost:{port}/draft/entries/{draft_id}" \
  -H "x-token: {x-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {"catalog_field": "title", "metadata_schema": "dct:title"},
      {"catalog_field": "description", "metadata_schema": "schema:description"}
    ]
  }'
```

---

### 4. 발행 (결재)

> **Service**: `metadata-ingestion` (port 8085)

```bash
curl -X POST "http://localhost:{port}/draft/entries/{draft_id}/publish" \
  -H "x-token: {x-token}"
```

**Response**:

```json
{
  "code": 102200,
  "message": "API Response Success",
  "result": {
    "catalog_entry_id": 31,
    "identifier": "550e8400-e29b-41d4-a716-446655440000",
    "title": "교통 데이터",
    "latest_snapshot_id": "a1b2c3d4e5f6..."
  },
  "description": "드래프트 1 발행 완료, 카탈로그 엔트리 31 생성"
}
```

---

### 5. 카탈로그 조회

> **Service**: `catalog-service` (port 8084)

#### 카탈로그 엔트리 조회

```bash
curl "http://localhost:{port}/catalog/entries/{catalog_entry_id}" \
  -H "x-token: {x-token}"
```

#### 카탈로그 검색

```bash
# 텍스트 검색
curl "http://localhost:{port}/catalog/entries?query=교통&limit=20" \
  -H "x-token: {x-token}"

# 키워드 필터링
curl "http://localhost:{port}/catalog/entries?keyword=dataset&limit=20" \
  -H "x-token: {x-token}"

# 주제 분류 필터링
curl "http://localhost:{port}/catalog/entries?theme=교통및물류&limit=20" \
  -H "x-token: {x-token}"
```

#### CSV 내보내기

```bash
curl "http://localhost:{port}/catalog/export/csv?limit=100" \
  -H "x-token: {x-token}" \
  -o catalog_entries.csv
```

---

## 부가 기능

### 수집 실행(Run) 조회

> **Service**: `metadata-ingestion` (port 8085)

```bash
# 목록 조회
curl "http://localhost:{port}/ingestion/runs" \
  -H "x-token: {x-token}"

# 상태별 필터링
curl "http://localhost:{port}/ingestion/runs?state=STORED" \
  -H "x-token: {x-token}"

# 상세 조회
curl "http://localhost:{port}/ingestion/runs/{run_id}" \
  -H "x-token: {x-token}"
```

### 드래프트 폐기

> **Service**: `metadata-ingestion` (port 8085)

발행하지 않고 드래프트 폐기

```bash
curl -X POST "http://localhost:{port}/draft/entries/{draft_id}/discard" \
  -H "x-token: {x-token}"
```

### 리니지(Lineage) 조회

> **Service**: `catalog-service` (port 8084)

데이터 흐름 추적: `file → snapshot → draft → catalog_entry`

```bash
# 리니지 그래프 조회
curl "http://localhost:{port}/lineage/graph/{snapshot_id}" \
  -H "x-token: {x-token}"

# 다운스트림 리니지 (snapshot → catalog_entry 방향)
curl "http://localhost:{port}/lineage/downstream/{snapshot_id}" \
  -H "x-token: {x-token}"

# 업스트림 리니지 (catalog_entry → snapshot 역방향)
curl "http://localhost:{port}/lineage/upstream/{catalog_entry_id}" \
  -H "x-token: {x-token}"
```

### RDF 표현 조회/다운로드

> **Service**: `catalog-service` (port 8084)

DCAT 표준 기반 JSON-LD 형식

```bash
# 조회
curl "http://localhost:{port}/catalog/entries/{catalog_entry_id}/rdf" \
  -H "x-token: {x-token}"

# 다운로드
curl "http://localhost:{port}/catalog/entries/{catalog_entry_id}/rdf/download" \
  -H "x-token: {x-token}" \
  -o catalog_entry_rdf.json
```

### 원본 메타데이터 조회

> **Service**: `catalog-service` (port 8084)

```bash
curl "http://localhost:{port}/catalog/entries/raw-metadata/{catalog_entry_id}" \
  -H "x-token: {x-token}"
```

### 컬럼 관계 생성

> **Service**: `metadata-ingestion` (port 8085)

```bash
curl -X POST "http://localhost:{port}/relation/" \
  -H "x-token: {x-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "catalog_column": "title",
    "metadata_column": "dc:title",
    "correlation": 0.95
  }'
```

### 컬럼 관계 조회

> **Service**: `catalog-service` (port 8084)

```bash
# 카탈로그 컬럼으로 관계 조회
curl "http://localhost:{port}/relation/catalog-column?catalog_column=title" \
  -H "x-token: {x-token}"

# 메타데이터 컬럼으로 관계 조회
curl "http://localhost:{port}/relation/metadata-column?metadata_column=dc:title" \
  -H "x-token: {x-token}"
```

### 메타데이터 엔트리 조회

> **Service**: `metadata-ingestion` (port 8085)

```bash
# 전체 메타데이터 목록 조회
curl "http://localhost:{port}/metadata/entries?limit=10" \
  -H "x-token: {x-token}"

# 텍스트 검색 (값, 스키마에서 검색)
curl "http://localhost:{port}/metadata/entries?query=title&limit=20" \
  -H "x-token: {x-token}"

# 메타데이터 스키마로 필터링
curl "http://localhost:{port}/metadata/entries?schema=dc:title&limit=20" \
  -H "x-token: {x-token}"

# UUID로 특정 메타데이터 엔트리 조회
curl "http://localhost:{port}/metadata/18e6f7bc-5791-488a-bc7b-d78b18e51dcd" \
  -H "x-token: {x-token}"
```

---

## Sample Metadata

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
