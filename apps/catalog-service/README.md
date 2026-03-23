# 카탈로그 서비스 (Catalog Service)

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green)](https://fastapi.tiangolo.com/)

## 개요

통합 메타데이터 카탈로그를 관리하고 질의 기능을 제공하는 서비스입니다. 이 서비스는 액티브 메타데이터 관리 시스템의 카탈로그 서비스 레이어를 담당하며, DCAT 표준 기반의 통합 메타데이터 카탈로그를 제공합니다.

## 주요 기능

- DCAT 3.0 표준 기반 통합 메타데이터 카탈로그 관리
- 메타데이터 검색 및 조회 기능
- 컬럼 간 연관성 분석 결과 기반 매핑 정보 제공
- RDF(JSON-LD) 형식 메타데이터 제공
- RESTful API를 통한 카탈로그 데이터 접근
- 리니지(Lineage) 추적
- CSV 내보내기

## 프로젝트 구조

```
catalog-service/
├── app/
│   ├── api/                        # API 라우터 및 엔드포인트
│   │   └── routers/
│   │       ├── catalog_entry.py    # 카탈로그 엔트리 API
│   │       ├── column_relation.py  # 컬럼 관계 API
│   │       ├── draft.py            # 드래프트 조회 API (읽기 전용)
│   │       └── lineage.py          # 리니지 API
│   ├── exceptions/                 # 예외 처리
│   ├── schemas/                    # Pydantic 스키마 정의
│   ├── src/                        # 핵심 비즈니스 로직
│   │   ├── catalog_entry/          # 카탈로그 엔트리
│   │   ├── catalog_entry_draft/    # 카탈로그 드래프트
│   │   ├── column_relation/        # 컬럼 관계
│   │   ├── lineage/                # 리니지 추적
│   │   ├── metadata_entry/         # 메타데이터 엔트리
│   │   └── metadata_snapshot/      # 메타데이터 스냅샷
│   ├── utils/                      # 공통 유틸리티
│   ├── config.py                   # 설정 관리
│   ├── db.py                       # 데이터베이스 연결
│   └── main.py                     # FastAPI 애플리케이션 진입점
├── pyproject.toml                  # 프로젝트 설정 및 의존성
└── README.md
```

## 설치 및 실행

### 로컬 개발 환경

1. **의존성 설치**

   ```bash
   uv sync
   ```

2. **서비스 실행**

   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8084
   ```

## API 문서

- Swagger UI: http://localhost:8084/docs
- `x-token` 기본값: `wisenut`

## 주요 API 엔드포인트

### 카탈로그 엔트리 (`/catalog`)

- `GET /catalog/entries`: 카탈로그 목록 조회/검색
- `GET /catalog/entries/{id}`: 카탈로그 엔트리 조회
- `GET /catalog/entries/{id}/rdf`: RDF(JSON-LD) 조회
- `GET /catalog/export/csv`: CSV 내보내기

### 카탈로그 드래프트 (`/draft`) - 읽기 전용

- `GET /draft/entries`: 드래프트 목록 조회
- `GET /draft/entries/{id}`: 드래프트 상세 조회

### 리니지 (`/lineage`)

- `GET /lineage/graph/{snapshot_id}`: 리니지 그래프 조회

### 컬럼 관계 (`/relation`)

- `GET /relation/catalog-column`: 카탈로그 컬럼으로 관계 조회
- `GET /relation/metadata-column`: 메타데이터 컬럼으로 관계 조회

상세 API 스펙은 Swagger UI 참조.
