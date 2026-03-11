"""Workflow result models."""

from uuid import UUID

from pydantic import BaseModel

from app.src.catalog_entry_draft.model import CatalogEntryDraft


class StorePhaseResult(BaseModel):
    """Result of Store Phase (metadata storage)."""

    snapshot_id: str
    run_id: UUID  # ingestion_run.run_id - needed for draft phase API call
    metadata_count: int


class DraftPhaseResult(BaseModel):
    """Result of Draft Phase (catalog draft creation)."""

    draft: CatalogEntryDraft
    mapping_version: str
