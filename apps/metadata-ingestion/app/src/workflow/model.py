"""Workflow result models."""

from uuid import UUID

from pydantic import BaseModel

from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_merge.model import CatalogMerge


class StorePhaseResult(BaseModel):
    """Result of Store Phase (metadata storage)."""

    snapshot_id: str
    run_id: UUID  # ingestion_run.run_id - needed for draft phase API call
    metadata_count: int


class DraftPhaseResult(BaseModel):
    """Result of Draft Phase (catalog draft creation)."""

    model_config = {"arbitrary_types_allowed": True}

    draft: CatalogEntryDraft
    mapping_version: str


class MergePhaseResult(BaseModel):
    """Result of Merge Phase (entity match + auto-publish decision)."""

    model_config = {"arbitrary_types_allowed": True}

    merge: CatalogMerge
    auto_published: bool = False
    catalog_entry_id: int | None = None
