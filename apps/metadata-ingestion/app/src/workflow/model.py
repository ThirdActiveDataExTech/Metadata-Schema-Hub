"""Workflow result models."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.src.catalog_entry_draft.model import CatalogEntryDraft


class StorePhaseResult(BaseModel):
    """Result of Store Phase (metadata storage)."""

    snapshot_id: str
    run_id: UUID  # ingestion_run.run_id - needed for draft phase API call
    metadata_count: int


class DraftPhaseResult(BaseModel):
    """Result of Draft Phase (catalog draft creation + merge)."""

    model_config = {"arbitrary_types_allowed": True}

    draft: CatalogEntryDraft
    mapping_version: str
    merge: Any = None  # CatalogMerge | None — Any to avoid circular import
    auto_published: bool = False
    catalog_entry_id: int | None = None
