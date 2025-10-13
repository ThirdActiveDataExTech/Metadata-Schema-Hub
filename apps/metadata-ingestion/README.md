# 메타데이터 수집 서비스 (Metadata Ingestion Service)

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green)](https://fastapi.tiangolo.com/)

## 개요

다양한 데이터 소스로부터 메타데이터를 수집, 전처리 및 저장하는 서비스입니다. 이 서비스는 액티브 메타데이터 관리 시스템의 데이터 수집 레이어를 담당합니다.

## 주요 기능

- 다양한 데이터 소스(공공데이터포털, 써드파티 데이터 등)로부터 메타데이터 수집
- 이기종 메타데이터 형식(DCAT/RDF, Schema.org/JSON 등)의 전처리 및 변환
- 메타데이터 품질 검증 및 보강
- PostgreSQL 데이터베이스에 구조화된 형태로 저장
- RESTful API를 통한 메타데이터 접근 및 관리

## 프로젝트 구조

```
metadata-ingestion/
├── app/
│   ├── api/                    # API 라우터 및 엔드포인트
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
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

## API 문서

- Swagger UI: http://localhost:8001/docs

## 주요 API 엔드포인트

- `GET /metadata/entries`: 메타데이터 엔트리 목록 조회
- `POST /metadata/entries`: 새로운 메타데이터 엔트리 생성
- `GET /metadata/entries/{id}`: 특정 메타데이터 엔트리 조회
- `PUT /metadata/entries/{id}`: 메타데이터 엔트리 업데이트
- `DELETE /metadata/entries/{id}`: 메타데이터 엔트리 삭제
- `GET /health`: 서비스 상태 확인
