-- catalog_merge: Entity match + field merge 결과 (단일 모델)
-- FK/index/constraint 없음 (이후 별도 반영)

CREATE TABLE IF NOT EXISTS catalog_merge
(
    id              BIGSERIAL PRIMARY KEY,
    draft_id        BIGINT       NOT NULL,
    target_entry_id BIGINT,
    merge_evidence  JSONB        NOT NULL DEFAULT '{}'::jsonb,
    mapping_score   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    decision        VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
    decided_at      TIMESTAMPTZ,
    decided_by      TEXT,
    created_at      TIMESTAMPTZ           DEFAULT now(),
    updated_at      TIMESTAMPTZ           DEFAULT now()
);

COMMENT ON TABLE catalog_merge IS 'Entity match + field merge result. Single model per architecture decision.';
COMMENT ON COLUMN catalog_merge.draft_id IS 'Source draft ID (catalog_entry_draft.id)';
COMMENT ON COLUMN catalog_merge.target_entry_id IS 'Target catalog entry ID. NULL = create new entry.';
COMMENT ON COLUMN catalog_merge.merge_evidence IS '3-key pattern: {searched_external_ids, candidates, recommended, decided}';
COMMENT ON COLUMN catalog_merge.mapping_score IS 'sum(decided.correlation) / len(content_fields). Used for auto-publish threshold.';
COMMENT ON COLUMN catalog_merge.decision IS 'PENDING / APPROVED / REJECTED';
COMMENT ON COLUMN catalog_merge.decided_by IS '"system_auto" for automatic, user ID for manual';
