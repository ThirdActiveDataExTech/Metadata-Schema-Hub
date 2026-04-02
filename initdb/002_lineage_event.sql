-- 데이터 출처 추적 이벤트 테이블
-- Upstream/Downstream 계보 조회 및 감사 이력용

CREATE TABLE IF NOT EXISTS lineage_event
(
    id               BIGSERIAL PRIMARY KEY,
    event_time       TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type       VARCHAR(20) NOT NULL,
    job_name         VARCHAR(50) NOT NULL,

    -- URI 배열 참조 ({schema}.{table}/{id} 형식)
    input_refs       TEXT[] NOT NULL DEFAULT '{}',
    output_refs      TEXT[] NOT NULL DEFAULT '{}',

    -- 선택적 메타데이터
    error_message    TEXT,

    created_at       TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT chk_event_type CHECK (event_type IN ('START', 'COMPLETE', 'FAIL')),
    CONSTRAINT chk_job_name CHECK (job_name IN ('store-phase', 'draft-phase', 'merge-phase', 'publish', 'discard'))
);

-- GIN 인덱스 (배열 검색용)
CREATE INDEX IF NOT EXISTS idx_lineage_input_refs ON lineage_event USING GIN (input_refs);
CREATE INDEX IF NOT EXISTS idx_lineage_output_refs ON lineage_event USING GIN (output_refs);
CREATE INDEX IF NOT EXISTS idx_lineage_event_time ON lineage_event (event_time DESC);

-- 테이블 설명
COMMENT ON TABLE lineage_event IS '데이터 출처 추적 이벤트. Upstream/Downstream 계보 조회 및 감사 이력용';

-- 컬럼 설명
COMMENT ON COLUMN lineage_event.id IS '고유 식별키 (Primary Key)';
COMMENT ON COLUMN lineage_event.event_time IS '이벤트 발생 시각';
COMMENT ON COLUMN lineage_event.event_type IS '이벤트 타입: START(시작), COMPLETE(완료), FAIL(실패)';
COMMENT ON COLUMN lineage_event.job_name IS '작업 이름: store-phase, draft-phase, merge-phase, publish, discard';
COMMENT ON COLUMN lineage_event.input_refs IS '입력 엔티티 URI 배열 ({schema}.{table}/{id} 형식)';
COMMENT ON COLUMN lineage_event.output_refs IS '출력 엔티티 URI 배열 ({schema}.{table}/{id} 형식)';
COMMENT ON COLUMN lineage_event.error_message IS '실패 시 에러 메시지';
COMMENT ON COLUMN lineage_event.created_at IS '레코드 생성 시각';
