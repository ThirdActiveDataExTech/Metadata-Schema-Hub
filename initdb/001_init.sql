CREATE TABLE IF NOT EXISTS users
(
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);


-- 메타데이터 변환용 테이블
CREATE TABLE IF NOT EXISTS metadata_entry
(
    id              SERIAL PRIMARY KEY,
    metadata_id     TEXT NOT NULL,              -- 메타데이터 id
    ingested_at     TIMESTAMPTZ DEFAULT now(),  -- 시스템 수집 일시
    metadata_schema TEXT NOT NULL,              -- 원본 메타데이터 스키마 명
    value           TEXT                        -- 원본 메타데이터 값
);

--- 필드별 COMMENT
COMMENT
ON TABLE metadata_entry IS 'RDF/JSON 메타데이터의 중첩 구조를 key-value 쌍으로 분해하여 저장하는 테이블.';

COMMENT
ON COLUMN metadata_entry.id IS '고유 식별키(Primary Key)';
COMMENT
ON COLUMN metadata_entry.metadata_id IS '메타데이터 식별키. 이 값이 동일하다면 같은 메타데이터에서 추출된 값.';
COMMENT
ON COLUMN metadata_entry.id IS '메타데이터 스키마 명.';
COMMENT
ON COLUMN metadata_entry.id IS '메타데이터 값.';


-- 데이터 카탈로그
CREATE TABLE IF NOT EXISTS catalog_entry
(
    id             SERIAL PRIMARY KEY,

    -- DCAT 3.0 필수 필드 구조화

    -- dataset, distribution 중복 필드
    title          TEXT,                      -- 제목 (dct:title)
    description    TEXT,                      -- 설명 (dct:description)
    issued         DATE,                      -- 발행일 (dct:issued)
    modified       DATE,                      -- 수정일 (dct:modified)

    -- dataset 필드
    identifier     TEXT  NOT NULL UNIQUE,     -- 고유 식별자 (dct:identifier), (dcat:Resource 속성)
    publisher      TEXT,                      -- 발행 기관 정보 (dct:publisher) 의 name 속성
    keyword        TEXT[],                    -- 키워드 리스트 (dcat:keyword), (dcat:Resource 속성)
    landing_page   TEXT,                      -- 웹 페이지 URL (dcat:landingPage), (dcat:Resource 속성)
    theme          TEXT[],                    -- 주제 분류 URI 또는 코드 (dcat:theme), (dcat:Resource 속성)

    -- distribution 필드
    access_url     TEXT,                      -- 배포판에 접근할 수 있는 URL (dcat:accessURL)

    -- 원본 메타데이터 저장용
    raw_metadata   JSONB NOT NULL,            -- 원본 메타데이터 전체(JSON-LD, schema.org, openapi 등)

    -- 수집/입력 메타 정보
    ingested_at    TIMESTAMPTZ DEFAULT now(), -- 시스템 수집 일시
    updated_at     TIMESTAMPTZ DEFAULT now()  -- 시스템 후처리 시 갱신 시각
);

-- 필드별 COMMENT
COMMENT
ON TABLE catalog_entry IS 'DCAT 기반 메타데이터 통합 저장 테이블. 다양한 입력 포맷을 수용하며, 핵심 필드는 컬럼화하고 원본은 JSONB로 보존.';

COMMENT
ON COLUMN catalog_entry.id IS '고유 식별키(Primary Key)';
COMMENT
ON COLUMN catalog_entry.title IS '데이터셋 또는 배포판 제목. dct:title.';
COMMENT
ON COLUMN catalog_entry.description IS '데이터셋 또는 배포판 설명. dct:description.';
COMMENT
ON COLUMN catalog_entry.issued IS '최초 발행일. dct:issued.';
COMMENT
ON COLUMN catalog_entry.modified IS '최종 수정일. dct:modified.';
COMMENT
ON COLUMN catalog_entry.identifier IS 'DCAT 기준 고유 식별자. 데이터셋 ID 역할. dct:identifier.';
COMMENT
ON COLUMN catalog_entry.publisher IS '발행처 이름 정보. dct:publisher.';
COMMENT
ON COLUMN catalog_entry.keyword IS '주제 키워드 배열. dcat:keyword.';
COMMENT
ON COLUMN catalog_entry.landing_page IS '데이터셋의 웹 페이지 URL. dcat:landingPage.';
COMMENT
ON COLUMN catalog_entry.theme IS '주제 분류 URI/코드 배열. dcat:theme.';
COMMENT
ON COLUMN catalog_entry.access_url IS '배포판에 접근할 수 있는 URL. dcat:accessURL.';
COMMENT
ON COLUMN catalog_entry.raw_metadata IS '입력된 원본 메타데이터 전체 (JSON-LD, schema.org, openapi 등).';
COMMENT
ON COLUMN catalog_entry.ingested_at IS '데이터가 수집되어 저장된 시간.';
COMMENT
ON COLUMN catalog_entry.updated_at IS '후처리, 재매핑 등으로 갱신된 시각.';
