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

| 열             | 형                                               | 주석                                                    |
|---------------|-------------------------------------------------|-------------------------------------------------------|
| id            | integer 자동 증가 [nextval('catalog_entry_id_seq')] |                                                       |
| identifier    | text                                            | DCAT 기준 고유 식별자. 데이터셋 ID 역할.                           |
| title         | text NULL                                       | 데이터셋 제목. dct:title.                                   |
| description   | text NULL                                       | 데이터셋 설명. dct:description.                             |
| issued        | date NULL                                       | 최초 발행일. dct:issued.                                   |
| modified      | date NULL                                       | 최종 수정일. dct:modified.                                 |
| publisher     | jsonb NULL                                      | 발행처 정보 (JSON 구조). dct:publisher.                      |
| keyword       | text[] NULL                                     | 주제 키워드. dcat:keyword.                                 |
| theme         | text[] NULL                                     | 주제 분류 URI/코드. dcat:theme.                             |
| raw_metadata  | jsonb                                           | 입력된 원본 메타데이터 전체 (JSON-LD, schema.org, openapi 등).     |
| source_format | text NULL                                       | 입력 메타데이터의 포맷 (ex. dcat_rdf, jsonld, schema, openapi). |
| ingested_at   | timestamptz NULL [now()]                        | 데이터가 수집되어 저장된 시간.                                     |
| updated_at    | timestamptz NULL [now()]                        | 후처리, 재매핑 등으로 갱신된 시각.                                  |

## 설계 근거

- DCAT 3.0 표준의 Dataset과 Distribution 클래스에서 권장되는 핵심 속성들을 스키마로 선정
- 다양한 데이터 소스와 포맷에서 호환성이 높고 결측치가 적은 컬럼을 우선 포함
- raw_metadata 필드를 통해 원본 메타데이터를 보존하여 확장성 확보

## 사용 방법 

```bash
$ docker compose up -d
```