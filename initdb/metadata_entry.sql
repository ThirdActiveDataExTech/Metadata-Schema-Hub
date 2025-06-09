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
