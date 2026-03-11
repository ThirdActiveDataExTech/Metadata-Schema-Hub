-- 워크플로우 상태 머신 테이블
-- 수집 프로세스 모니터링 및 재처리 대상 식별용
CREATE TABLE IF NOT EXISTS ingestion_run
(
    run_id           UUID PRIMARY KEY,
    snapshot_id      TEXT NOT NULL,                                              -- 스냅샷 참조
    state            VARCHAR(20) NOT NULL DEFAULT 'STORED',                      -- 워크플로우 상태: STORED/DRAFTED/FAILED
    mapping_version  VARCHAR(100) NOT NULL,                                      -- 매핑 로직 버전 (컨테이너 태그)
    created_at       TIMESTAMPTZ DEFAULT now(),                                  -- 작업 생성 시각 (Store Phase 시작)
    updated_at       TIMESTAMPTZ DEFAULT now(),                                  -- 마지막 상태 변경 시각
    error            TEXT,                                                       -- 실패 시 오류 메시지
    draft_id         BIGINT,                                                     -- 생성된 draft 참조 (Draft Phase 완료 후 설정)

    CONSTRAINT chk_ingestion_run_state CHECK (state IN ('STORED', 'DRAFTED', 'FAILED'))
);

-- 빠른 조회를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_ingestion_run_snapshot_id ON ingestion_run(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_run_state ON ingestion_run(state);
CREATE INDEX IF NOT EXISTS idx_ingestion_run_created_at ON ingestion_run(created_at);

-- 테이블 설명
COMMENT ON TABLE ingestion_run IS '워크플로우 상태 머신. 수집 프로세스 모니터링 및 재처리 대상 식별용';

-- 컬럼 설명
COMMENT ON COLUMN ingestion_run.run_id IS 'run_id (UUID, 앱에서 생성)';
COMMENT ON COLUMN ingestion_run.snapshot_id IS '불변 메타데이터 스냅샷 참조';
COMMENT ON COLUMN ingestion_run.state IS '워크플로우 상태: STORED (Store Phase 완료), DRAFTED (Draft Phase 완료), FAILED (실패)';
COMMENT ON COLUMN ingestion_run.mapping_version IS '매핑에 사용된 서비스 버전 (예: v1.2601.20-dev-5f937c57)';
COMMENT ON COLUMN ingestion_run.created_at IS '작업 생성 시각 (Store Phase 시작 시점)';
COMMENT ON COLUMN ingestion_run.updated_at IS '마지막 상태 변경 시각';
COMMENT ON COLUMN ingestion_run.error IS '실패 시 오류 상세 메시지';
COMMENT ON COLUMN ingestion_run.draft_id IS 'Draft Phase에서 생성된 catalog_entry_draft 참조';
