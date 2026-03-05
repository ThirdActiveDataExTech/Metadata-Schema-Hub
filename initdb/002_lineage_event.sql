-- 리니지 이벤트 테이블 (OpenLineage 호환)
-- 메타데이터 처리 워크플로우 추적을 위한 이벤트 저장
CREATE TABLE IF NOT EXISTS lineage_event
(
    id               BIGSERIAL PRIMARY KEY,           -- 고유 식별키
    event_time       TIMESTAMPTZ NOT NULL,            -- 이벤트 발생 시각
    event_type       VARCHAR(20) NOT NULL,            -- 이벤트 타입 (START, RUNNING, COMPLETE, FAIL, ABORT, OTHER)
    run_id           UUID NOT NULL,                   -- OpenLineage Run UUID (UUIDv4)
    job_namespace    VARCHAR(255) NOT NULL DEFAULT 'wisenut-amm', -- OpenLineage Job 네임스페이스
    job_name         VARCHAR(255) NOT NULL,           -- OpenLineage Job 이름
    event_payload    JSONB NOT NULL,                  -- 전체 OpenLineage RunEvent JSON 페이로드

    -- 쿼리 최적화를 위한 내부 참조 필드
    snapshot_id      TEXT,                            -- 메타데이터 스냅샷 참조
    draft_id         BIGINT,                          -- 카탈로그 엔트리 초안 참조
    catalog_entry_id INTEGER,                         -- 카탈로그 엔트리 참조
    ingestion_run_id BIGINT,                          -- 수집 실행 참조

    created_at       TIMESTAMPTZ DEFAULT now(),       -- 레코드 생성 시각

    -- 제약 조건
    CONSTRAINT chk_lineage_event_type CHECK (event_type IN ('START', 'RUNNING', 'COMPLETE', 'FAIL', 'ABORT', 'OTHER'))
);

-- 조회 패턴별 인덱스
CREATE INDEX IF NOT EXISTS idx_lineage_event_run_id ON lineage_event(run_id);
CREATE INDEX IF NOT EXISTS idx_lineage_event_job ON lineage_event(job_namespace, job_name);
CREATE INDEX IF NOT EXISTS idx_lineage_event_time ON lineage_event(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_lineage_event_type ON lineage_event(event_type);

-- 내부 참조 필드 인덱스 (부분 인덱스)
CREATE INDEX IF NOT EXISTS idx_lineage_event_snapshot_id ON lineage_event(snapshot_id) WHERE snapshot_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lineage_event_draft_id ON lineage_event(draft_id) WHERE draft_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lineage_event_catalog_entry_id ON lineage_event(catalog_entry_id) WHERE catalog_entry_id IS NOT NULL;

-- JSONB 페이로드 검색용 GIN 인덱스
CREATE INDEX IF NOT EXISTS idx_lineage_event_payload ON lineage_event USING GIN (event_payload jsonb_path_ops);

-- 테이블 설명
COMMENT ON TABLE lineage_event IS 'OpenLineage 호환 리니지 이벤트 저장 테이블. 메타데이터 처리 워크플로우의 실행 이력 추적.';

-- 컬럼 설명
COMMENT ON COLUMN lineage_event.id IS '고유 식별키 (Primary Key)';
COMMENT ON COLUMN lineage_event.event_time IS '이벤트 발생 시각 (OpenLineage eventTime)';
COMMENT ON COLUMN lineage_event.event_type IS '이벤트 타입: START(시작), RUNNING(실행중), COMPLETE(완료), FAIL(실패), ABORT(중단), OTHER(기타)';
COMMENT ON COLUMN lineage_event.run_id IS 'OpenLineage Run UUID. 동일 실행의 이벤트들을 그룹화.';
COMMENT ON COLUMN lineage_event.job_namespace IS 'OpenLineage Job 네임스페이스. 기본값: wisenut-amm';
COMMENT ON COLUMN lineage_event.job_name IS 'OpenLineage Job 이름. 워크플로우 단계 식별.';
COMMENT ON COLUMN lineage_event.event_payload IS '전체 OpenLineage RunEvent JSON. inputs, outputs, facets 포함.';
COMMENT ON COLUMN lineage_event.snapshot_id IS '관련 메타데이터 스냅샷 ID 참조 (쿼리 최적화용)';
COMMENT ON COLUMN lineage_event.draft_id IS '관련 카탈로그 엔트리 초안 ID 참조 (쿼리 최적화용)';
COMMENT ON COLUMN lineage_event.catalog_entry_id IS '관련 카탈로그 엔트리 ID 참조 (쿼리 최적화용)';
COMMENT ON COLUMN lineage_event.ingestion_run_id IS '관련 수집 실행 ID 참조 (쿼리 최적화용)';
COMMENT ON COLUMN lineage_event.created_at IS '레코드 생성 시각 (시스템 자동 기록)';
