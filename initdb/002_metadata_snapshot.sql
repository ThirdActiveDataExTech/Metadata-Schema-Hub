-- 메타데이터 스냅샷 저장 테이블
CREATE TABLE IF NOT EXISTS metadata_snapshot
(
    snapshot_id        TEXT PRIMARY KEY,              -- 고유 식별자 (urn:wisenut:metadata:{timestamp}-{hash12})
    payload_sha256     TEXT NOT NULL,                 -- 콘텐츠 SHA256 해시 (중복 제거용)
    ingested_at        TIMESTAMPTZ DEFAULT now(),     -- 스냅샷 생성 시각 (UTC)
    storage_key        TEXT NOT NULL,                 -- 스토리지 상대 경로
    original_filename  TEXT                           -- 원본 파일명 (선택)
);

-- 빠른 조회를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_payload_sha256 ON metadata_snapshot(payload_sha256);
CREATE INDEX IF NOT EXISTS idx_ingested_at ON metadata_snapshot(ingested_at);

-- 테이블 설명
COMMENT ON TABLE metadata_snapshot IS '불변 메타데이터 스냅샷 (snapshot_id를 자연키로 사용)';

-- 컬럼 설명
COMMENT ON COLUMN metadata_snapshot.snapshot_id IS '고유 식별자: urn:wisenut:metadata:{timestamp}-{hash12}';
COMMENT ON COLUMN metadata_snapshot.payload_sha256 IS '중복 제거를 위한 콘텐츠 SHA256 해시';
COMMENT ON COLUMN metadata_snapshot.ingested_at IS '스냅샷 생성 시각 (UTC)';
COMMENT ON COLUMN metadata_snapshot.storage_key IS '스토리지 상대 경로: {YYYY}/{MM}/{DD}/{timestamp}-{hash12}.{ext}';
COMMENT ON COLUMN metadata_snapshot.original_filename IS '참고용 원본 파일명 (nullable)';
