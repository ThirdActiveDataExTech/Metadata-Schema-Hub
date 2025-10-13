# 카탈로그 서비스 (Catalog Service)

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green)](https://fastapi.tiangolo.com/)

## 개요

통합 메타데이터 카탈로그를 관리하고 질의 기능을 제공하는 서비스입니다. 이 서비스는 액티브 메타데이터 관리 시스템의 카탈로그 서비스 레이어를 담당하며, DCAT 표준 기반의 통합 메타데이터 카탈로그를 제공합니다.

## 주요 기능

- DCAT 3.0 표준 기반 통합 메타데이터 카탈로그 관리
- 메타데이터 검색 및 조회 기능
- 컬럼 간 연관성 분석 결과 기반 매핑 정보 제공
- 메타데이터 품질 검증 및 보강
- RESTful API를 통한 카탈로그 데이터 접근


## 프로젝트 구조

```
catalog-service/
├── app/
│   ├── api/                    # API 라우터 및 엔드포인트
│   │   └── routers/           # 개별 리소스별 라우터
│   │       ├── catalog_entry.py    # 카탈로그 엔트리 API
│   │       └── column_relation.py  # 컬럼 관계 API
│   ├── exceptions/             # 예외 처리
│   ├── schemas/                # Pydantic 스키마 정의
│   ├── src/                    # 핵심 비즈니스 로직
│   │   ├── util/              # 유틸리티 함수
│   │   ├── file_converter/    # 파일 변환 도구
│   │   ├── workflow/          # 워크플로우 관리
│   │   └── metadata_entry/    # 메타데이터 엔트리 처리
│   ├── utils/                 # 공통 유틸리티
│   ├── config.py              # 설정 관리
│   ├── db.py                  # 데이터베이스 연결
│   └── main.py                # FastAPI 애플리케이션 진입점
├── pyproject.toml             # 프로젝트 설정 및 의존성
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
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8002
   ```

## API 문서

- Swagger UI: http://localhost:8002/docs

## 주요 API 엔드포인트

### 카탈로그 엔트리
- `GET /catalog/entries`: 카탈로그 엔트리 목록 조회
- `POST /catalog/entries`: 새로운 카탈로그 엔트리 생성
- `GET /catalog/entries/{id}`: 특정 카탈로그 엔트리 조회
- `PUT /catalog/entries/{id}`: 카탈로그 엔트리 업데이트
- `DELETE /catalog/entries/{id}`: 카탈로그 엔트리 삭제

### 컬럼 관계
- `GET /relation/`: 컬럼 관계 정보 조회
- `POST /relation/`: 새로운 컬럼 관계 생성
- `GET /relation/{id}`: 특정 컬럼 관계 조회

### 기타
- `GET /health`: 서비스 상태 확인
