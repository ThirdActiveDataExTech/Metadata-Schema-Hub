# 액티브 메타데이터 스키마

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)
[![Postgres](https://img.shields.io/badge/Postgres-17.4-%23316192)]([#](https://hub.docker.com/layers/library/postgres/17.4/images/sha256-48f04a5009fe444f00178907dd32f6df809246a959468f72248284752f31dadd))
[![Postgres](https://img.shields.io/badge/Postgres-%23316192.svg?logo=postgresql&logoColor=white)]([#](https://www.postgresql.org/download/))

> **[공개 SW] 모노레포**: 액티브 메타데이터 관리 + 통합 데이터 카탈로그 생성  
> **성과지표**: 관계형 데이터 유사 속성 탐지율

## 개요

![아키텍처](amd.drawio.svg)

다양한 데이터 소스의 메타데이터를 수집, 통합, 변환 및 저장하기 위한 스키마입니다.

이 시스템은 서로 다른 형식의 메타데이터를 표준화된 통합 카탈로그로 변환하여 조직 전체의 데이터 자산을 효율적으로 관리하고 활용할 수 있도록 지원합니다.

## 주요 기능

- 다양한 데이터 소스(공공데이터포털, 써드파티 데이터 등)로부터 메타데이터 수집
- 이기종 메타데이터 형식(DCAT/RDF, Schema.org/JSON 등)의 통합 변환
- 메타데이터 품질 검증 및 보강
- 확장 가능한 메타데이터 저장소 구축
- 메타데이터 검색 및 조회 기능
- [컬럼 간 연관성 분석](https://github.com/ThirdActiveDataExTech/RelationalSchemaMatching) 결과 기반 매핑

## 기대 효과

- 다양한 소스의 메타데이터를 일관된 방식으로 통합 관리
- 메타데이터 수집 및 처리 자동화로 운영 효율성 증대
- 메타데이터 기반 데이터 검색성 및 활용성 향상
- 데이터 카탈로그 구축을 통한 조직 전체 데이터 자산 가시성 확보

---

# 스키마 구조

## 1. catalog_entry 테이블

**DCAT 기반 메타데이터 통합 저장 테이블**

| 컬럼명 | 데이터타입 | 제약조건 | 설명 |
|--------|------------|----------|------|
| id | SERIAL | PRIMARY KEY | 고유 식별키 |
| title | TEXT | | 데이터셋/배포판 제목 (dct:title) |
| description | TEXT | | 데이터셋/배포판 설명 (dct:description) |
| issued | DATE | | 최초 발행일 (dct:issued) |
| modified | DATE | | 최종 수정일 (dct:modified) |
| identifier | TEXT | NOT NULL UNIQUE | DCAT 기준 고유 식별자 (dct:identifier) |
| publisher | TEXT | | 발행처 이름 정보 (dct:publisher) |
| keyword | TEXT[] | | 주제 키워드 배열 (dcat:keyword) |
| landing_page | TEXT | | 데이터셋 웹 페이지 URL (dcat:landingPage) |
| theme | TEXT[] | | 주제 분류 URI/코드 배열 (dcat:theme) |
| access_url | TEXT | | 배포판 접근 URL (dcat:accessURL) |
| raw_metadata | JSONB | NOT NULL | 원본 메타데이터 전체 (JSON-LD, schema.org, openapi) |
| ingested_at | TIMESTAMPTZ | DEFAULT now() | 데이터 수집 저장 시간 |
| updated_at | TIMESTAMPTZ | DEFAULT now() | 후처리/재매핑 갱신 시각 |

## 2. metadata_entry 테이블

**RDF/JSON 메타데이터의 중첩 구조를 key-value 쌍으로 분해하여 저장하는 테이블**

| 컬럼명 | 데이터타입 | 제약조건 | 설명 |
|--------|------------|----------|------|
| id | SERIAL | PRIMARY KEY | 고유 식별키 |
| metadata_id | TEXT | NOT NULL | 메타데이터 식별키 (동일 값 = 같은 메타데이터에서 추출) |
| ingested_at | TIMESTAMPTZ | DEFAULT now() | 시스템 수집 일시 |
| metadata_schema | TEXT | NOT NULL | 원본 메타데이터 스키마명 |
| value | TEXT | | 원본 메타데이터 값 |

## 3. column_relation 테이블

**카탈로그 컬럼과 메타데이터 컬럼 간의 매핑 관계 및 연관성 점수를 저장하는 테이블**

| 컬럼명 | 데이터타입 | 제약조건 | 설명 |
|--------|------------|----------|------|
| id | SERIAL | PRIMARY KEY | 고유 식별키 |
| catalog_column | TEXT | NOT NULL | 카탈로그 테이블의 컬럼명 |
| correlation | REAL | NOT NULL | 컬럼 간 연관성 점수 (0.0-1.0 범위) |
| metadata_column | TEXT | NOT NULL | 메타데이터 테이블의 컬럼명 |

## 설계 근거

### catalog_entry
- DCAT 3.0 표준의 Dataset과 Distribution 클래스에서 권장되는 핵심 속성들을 스키마로 선정
- 다양한 데이터 소스와 포맷에서 호환성이 높고 결측치가 적은 컬럼을 우선 포함
- raw_metadata 필드를 통해 원본 메타데이터를 보존하여 확장성 확보

### metadata_entry
- 복잡한 중첩 구조의 메타데이터를 평면화하여 분석 및 처리 용이성 확보
- 스키마별 값 분리를 통한 유연한 데이터 변환 및 매핑 지원

### column_relation
- 컬럼 간 연관성 분석 결과 기반 매핑 자동화를 위한 예측 결과 저장
- 메타데이터와 카탈로그 간 의미적 연관성 정량화

### catalog_entry_draft
- 매핑 결과의 검토/승인 워크플로우 지원
- mapping_evidence 필드로 매핑 결정 근거 투명성 확보

### lineage_event
- 데이터 출처 추적을 위한 이벤트 기반 계보 관리
- Upstream/Downstream 관계 조회 및 감사 이력 지원

---

## 레포지토리 구조

```
active-metadata-management/
├── apps/
│   ├── metadata-ingestion/         # 데이터 수집 / 처리 레이어
│   ├── catalog-service/            # 카탈로그 서비스 레이어
│   └── workflow-ui/                # 워크플로우 시각화 UI (React/Vite)
├── packages/
│   └── active-metadata/            # 공유 DB 모델 패키지 (SQLModel)
├── initdb/                         # 데이터베이스 스키마 정의
│   ├── 001_init.sql                # 초기 설정
│   ├── 002_catalog_entry.sql       # 통합 카탈로그 DB 스키마
│   ├── 002_catalog_entry_draft.sql # 카탈로그 드래프트 스키마
│   ├── 002_metadata_entry.sql      # 메타데이터 스키마 DB 스키마
│   ├── 002_metadata_snapshot.sql   # 불변 스냅샷 스키마
│   ├── 002_column_relation.sql     # 스키마 관계 DB 스키마
│   ├── 002_ingestion_run.sql       # 워크플로우 상태 머신 스키마
│   ├── 002_lineage_event.sql       # 데이터 계보 추적 스키마
│   └── 003_initialize_column_relation.sql  # 컬럼 관계 초기화
├── sample/                         # 테스트용 메타데이터 샘플
├── scripts/                        # 유틸리티 스크립트
└── docker-compose.yaml             # 전체 시스템 오케스트레이션
```

## 서비스 아키텍처

| 서비스 | 포트 | 설명 |
|--------|------|------|
| metadata-ingestion | 8085 | 스키마 및 메타데이터 수집/전처리 |
| catalog-service | 8084 | 통합 카탈로그 질의 및 데이터 변환 |
| workflow-ui | 3000 | 워크플로우 시각화 UI |
| PostgreSQL 17.4 | 5432 | 메타데이터/카탈로그/계보 DB |
| Adminer | 8888 | DB 웹 클라이언트 (개발용) |

---

## 사용 방법

```bash
$ docker compose up -d
```

### 데이터 처리 흐름

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Ingest    │───▶│   Store     │───▶│   Draft     │───▶│  Publish/   │
│   (Upload)  │    │   Phase     │    │   Phase     │    │  Discard    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                         │                  │                   │
                         ▼                  ▼                   ▼
                   metadata_snapshot  catalog_entry_draft  catalog_entry
                   ingestion_run      ingestion_run        lineage_event
                   lineage_event      lineage_event
```

1. **Store Phase**: 원본 메타데이터를 `metadata_snapshot`에 불변 저장, `ingestion_run` 상태 → STORED
2. **Draft Phase**: 자동 매핑으로 `catalog_entry_draft` 생성 (PENDING), `ingestion_run` 상태 → DRAFTED
3. **Publish/Discard**: 검토 후 `catalog_entry`로 게시 또는 폐기, 모든 작업은 `lineage_event`에 기록
