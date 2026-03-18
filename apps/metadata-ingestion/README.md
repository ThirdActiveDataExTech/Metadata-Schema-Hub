# 메타데이터 수집 서비스 (Metadata Ingestion Service)

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green)](https://fastapi.tiangolo.com/)

## 개요

다양한 데이터 소스로부터 메타데이터를 수집, 전처리 및 저장하는 서비스입니다. 이 서비스는 액티브 메타데이터 관리 시스템의 데이터 수집 레이어를 담당합니다.

## 주요 기능

- 3단계 수집 워크플로우: 메타데이터 파일 업로드 → 드래프트 생성 → 드래프트 검토 및 카탈로그 발행
- 이기종 메타데이터 형식(DCAT/RDF, Schema.org/JSON 등)의 전처리 및 변환
- 드래프트 기반 매핑 검토/수정
- 매핑 증거 제공
- RESTful API를 통한 메타데이터 접근 및 관리

## 프로젝트 구조

```
metadata-ingestion/
├── app/
│   ├── api/                        # API 라우터 및 엔드포인트
│   │   └── routers/
│   │       ├── column_relation.py  # 컬럼 관계 API
│   │       ├── draft.py            # 드래프트 관리 API
│   │       ├── ingestion.py        # 메타데이터 수집 워크플로우 API
│   │       └── metadata_entry.py   # 메타데이터 엔트리 조회 API
│   ├── exceptions/                 # 예외 처리
│   ├── schemas/                    # Pydantic 스키마 정의
│   ├── src/                        # 핵심 비즈니스 로직
│   │   ├── catalog_entry/          # 카탈로그 엔트리
│   │   ├── catalog_entry_draft/    # 카탈로그 드래프트
│   │   ├── column_relation/        # 컬럼 관계
│   │   ├── events/                 # 이벤트 처리
│   │   ├── file_converter/         # 파일 변환 (DCAT/Schema.org)
│   │   ├── ingestion_run/          # 수집 실행 관리
│   │   ├── lineage/                # 리니지 추적
│   │   ├── metadata_entry/         # 메타데이터 엔트리
│   │   ├── metadata_snapshot/      # 메타데이터 스냅샷
│   │   └── workflow/               # 워크플로우 관리
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
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8085
   ```

## API 문서

- Swagger UI: `http://localhost:8085/docs`
- `x-token` 기본값: `wisenut`

## 주요 API 엔드포인트

### 수집 워크플로우 (`/ingestion`)

- `POST /ingestion/store`: 메타데이터 파일 업로드 및 저장
- `POST /ingestion/draft/{run_id}`: 드래프트 생성
- `GET /ingestion/runs`: 수집 실행 목록 조회

### 드래프트 관리 (`/draft`)

- `GET /draft/entries/{id}`: 드래프트 조회
- `GET /draft/entries/{id}/evidence`: 매핑 증거 조회
- `PATCH /draft/entries/{id}`: 드래프트 수정
- `POST /draft/entries/{id}/publish`: 발행
- `POST /draft/entries/{id}/discard`: 폐기

### 메타데이터 엔트리 (`/metadata`)

- `GET /metadata/entries`: 메타데이터 목록 조회/검색
- `GET /metadata/{uuid}`: 특정 메타데이터 엔트리 조회

### 컬럼 관계 (`/relation`)

- `POST /relation/`: 컬럼 관계 생성
- `GET /relation/catalog-column`: 카탈로그 컬럼으로 관계 조회
- `GET /relation/metadata-column`: 메타데이터 컬럼으로 관계 조회

상세 API 스펙은 Swagger UI 참조.
