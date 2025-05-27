# 액티브 메타데이터 스키마

[![Python Version](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/)
[![Postgres](https://img.shields.io/badge/Postgres-17.4-%23316192)]([#](https://hub.docker.com/layers/library/postgres/17.4/images/sha256-48f04a5009fe444f00178907dd32f6df809246a959468f72248284752f31dadd))
[![Postgres](https://img.shields.io/badge/Postgres-%23316192.svg?logo=postgresql&logoColor=white)]([#](https://www.postgresql.org/download/))

다양한 데이터 소스의 메타데이터를 수집, 통합, 변환 및 저장하기 위한 스키마 입니다. 

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

---

# 스키마 정의

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

* `/initdb/001_init.sql` DDL 기반으로 스키마가 정의됨
* 해당 테이블이 없을 경우, 로직이 실패할 수 있음

## 설계 근거

- DCAT 3.0 표준의 Dataset과 Distribution 클래스에서 권장되는 핵심 속성들을 스키마로 선정
- 다양한 데이터 소스와 포맷에서 호환성이 높고 결측치가 적은 컬럼을 우선 포함
- raw_metadata 필드를 통해 원본 메타데이터를 보존하여 확장성 확보

## 사용 방법 

```bash
$ docker compose up -d
```