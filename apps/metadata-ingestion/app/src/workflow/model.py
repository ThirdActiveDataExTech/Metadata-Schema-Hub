"""Workflow result models."""

from pydantic import BaseModel

from app.src.catalog_entry_draft.model import CatalogEntryDraft


class StorePhaseResult(BaseModel):
    """Result of Store Phase (metadata storage)."""

    snapshot_id: str
    run_id: int
    metadata_count: int


class DraftPhaseResult(BaseModel):
    """Result of Draft Phase (catalog draft creation)."""

    draft: CatalogEntryDraft
    run_id: int
    mapping_version: str
