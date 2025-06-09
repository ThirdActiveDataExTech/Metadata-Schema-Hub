-- 메타데이터 - 카탈로그 컬럼 관계 테이블
CREATE TABLE IF NOT EXISTS column_relation
(
    id              SERIAL PRIMARY KEY,
    catalog_column  TEXT NOT NULL,          -- 카탈로그 컬럼 명
    correlation     REAL NOT NULL,          -- 카탈로그 컬럼 - 메타데이터 컬럼 연관성, 0-1 Float
    metadata_column TEXT NOT NULL           -- 메타데이터 컬럼 명
);

-- 필드별 COMMENT
COMMENT ON TABLE column_relation IS '카탈로그 컬럼과 메타데이터 컬럼 간의 매핑 관계 및 연관성 점수를 저장하는 테이블. ML 예측 결과 기반.';

COMMENT ON COLUMN column_relation.id IS '고유 식별키(Primary Key)';
COMMENT ON COLUMN column_relation.catalog_column IS '카탈로그 테이블의 컬럼명';
COMMENT ON COLUMN column_relation.correlation IS '컬럼 간 연관성 점수 (0.0-1.0 범위의 ML 예측값)';
COMMENT ON COLUMN column_relation.metadata_column IS '메타데이터 테이블의 컬럼명';