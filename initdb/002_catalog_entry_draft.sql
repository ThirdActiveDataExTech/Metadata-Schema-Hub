-- 카탈로그 엔트리 드래프트 테이블
-- 매핑 근거(evidence)와 함께 승인 대기 중인 드래프트 저장
CREATE TABLE IF NOT EXISTS catalog_entry_draft
(
    id                BIGSERIAL PRIMARY KEY,                                      -- 드래프트 고유 식별자
    snapshot_id       TEXT NOT NULL,                                              -- 원본 스냅샷 참조
    mapping_version   VARCHAR(100) NOT NULL,                                      -- 매핑 로직 버전
    created_at        TIMESTAMPTZ DEFAULT now(),                                  -- 드래프트 생성 시각
    updated_at        TIMESTAMPTZ DEFAULT now(),                                  -- 마지막 수정 시각

    -- DCAT 드래프트 필드 (catalog_entry와 동일 구조)
    title             TEXT,                                                       -- 제목 (dct:title)
    description       TEXT,                                                       -- 설명 (dct:description)
    issued            DATE,                                                       -- 발행일 (dct:issued)
    modified          DATE,                                                       -- 수정일 (dct:modified)
    publisher         TEXT,                                                       -- 발행 기관 (dct:publisher)
    keyword           TEXT[],                                                     -- 키워드 배열 (dcat:keyword)
    theme             TEXT[],                                                     -- 주제 분류 배열 (dcat:theme)
    landing_page      TEXT,                                                       -- 웹 페이지 URL (dcat:landingPage)
    access_url        TEXT,                                                       -- 접근 URL (dcat:accessURL)

    -- 매핑 근거 (필드별 top-k 후보와 correlation 점수)
    mapping_evidence  JSONB NOT NULL DEFAULT '{}'::jsonb                          -- 매핑 결정 근거 저장
);

-- 빠른 조회를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_catalog_entry_draft_snapshot_id ON catalog_entry_draft(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_catalog_entry_draft_mapping_version ON catalog_entry_draft(mapping_version);
CREATE INDEX IF NOT EXISTS idx_catalog_entry_draft_created_at ON catalog_entry_draft(created_at);

-- 테이블 설명
COMMENT ON TABLE catalog_entry_draft IS '매핑 근거와 함께 저장된 카탈로그 엔트리 드래프트 (승인/게시 대기)';

-- 컬럼 설명
COMMENT ON COLUMN catalog_entry_draft.id IS '자동 생성 드래프트 고유 식별자';
COMMENT ON COLUMN catalog_entry_draft.snapshot_id IS '원본 메타데이터 스냅샷 참조';
COMMENT ON COLUMN catalog_entry_draft.mapping_version IS '드래프트 생성에 사용된 매핑 로직 버전';
COMMENT ON COLUMN catalog_entry_draft.mapping_evidence IS '필드별 top-k 매핑 후보와 correlation 점수를 담은 JSONB';
