"""Business logic for CatalogEntryDraft."""

from typing import Any, Optional

from active_metadata import CatalogEntryDraftBase, convert_field_types
from active_metadata.models import DraftStatus
from sqlmodel import Session

from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_entry_draft.model import (
    CatalogEntryDraft,
    CatalogEntryDraftCreate,
    MappingCandidate,
    MappingEvidence,
)
from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository
from app.src.column_relation.model import ColumnRelation
from app.src.metadata_entry.model import MetadataEntry


class CatalogEntryDraftService:
    """CatalogEntryDraft service."""

    def __init__(
        self,
        repository: CatalogEntryDraftRepository,
        catalog_entry_service: Optional[CatalogEntryService] = None,
    ):
        """Initialize with repository and optional catalog service for publish."""
        self.repository = repository
        self.catalog_entry_service = catalog_entry_service

    def build_mapping_with_evidence(
        self,
        metadata_entries: list[MetadataEntry],
        relations: list[ColumnRelation],
        top_k: int = 3,
    ) -> dict[str, MappingEvidence]:
        """Build mapping evidence per catalog column.

        Returns:
            Evidence map: catalog_column -> MappingEvidence (contains selected value + alternatives)
        """
        # Build metadata lookup dict
        metadata_dict = {entry.metadata_schema: entry.value for entry in metadata_entries}

        # Group relations by catalog_column, sorted by correlation
        column_candidates: dict[str, list[MappingCandidate]] = {}
        for relation in sorted(relations, key=lambda r: r.correlation, reverse=True):
            if relation.catalog_column not in column_candidates:
                column_candidates[relation.catalog_column] = []

            if relation.metadata_column in metadata_dict:
                column_candidates[relation.catalog_column].append(
                    MappingCandidate(
                        metadata_column=relation.metadata_column,
                        correlation=relation.correlation,
                        value=metadata_dict[relation.metadata_column],
                    )
                )

        # Build evidence (top-k candidates per column)
        evidence_map: dict[str, MappingEvidence] = {}
        for catalog_column, candidates in column_candidates.items():
            if candidates:
                evidence_map[catalog_column] = MappingEvidence(
                    selected=candidates[0],
                    alternatives=candidates[1:top_k] if len(candidates) > 1 else [],
                )

        return evidence_map

    def create_draft(
        self,
        db: Session,
        snapshot_id: str,
        mapping_version: str,
        metadata_entries: list[MetadataEntry],
        relations: list[ColumnRelation],
    ) -> CatalogEntryDraft:
        """Create draft with automatic mapping (Draft Phase)."""
        evidence_map = self.build_mapping_with_evidence(metadata_entries, relations)

        # Extract mapped fields from evidence (top-1 value)
        mapped_fields = {col: ev.selected.value for col, ev in evidence_map.items()}

        # Convert field types (str -> date, str -> list[str])
        typed_fields = convert_field_types(
            mapped_fields,
            list_fields=CatalogEntryDraftBase.get_list_fields(),
            date_fields=CatalogEntryDraftBase.get_date_fields(),
        )

        # Convert evidence to dict for JSONB storage
        mapping_evidence = {col: ev.model_dump() for col, ev in evidence_map.items()}

        create_dto = CatalogEntryDraftCreate(
            snapshot_id=snapshot_id,
            mapping_version=mapping_version,
            mapping_evidence=mapping_evidence,
            **typed_fields,
        )

        draft = CatalogEntryDraft.model_validate(create_dto.model_dump())
        return self.repository.save(db, draft)

    def get_draft(self, db: Session, draft_id: int) -> Optional[CatalogEntryDraft]:
        """Get draft by ID."""
        return self.repository.find_by_id(db, draft_id)

    def get_drafts_by_snapshot(self, db: Session, snapshot_id: str) -> list[CatalogEntryDraft]:
        """Get all drafts for a snapshot."""
        return self.repository.find_by_snapshot_id(db, snapshot_id)

    def get_all_drafts(self, db: Session, limit: int = 100, offset: int = 0) -> list[CatalogEntryDraft]:
        """Get all drafts with pagination."""
        return self.repository.find_all(db, limit, offset)

    def get_mapping_evidence(self, db: Session, draft_id: int) -> Optional[dict[str, Any]]:
        """Get mapping evidence for a draft."""
        draft = self.get_draft(db, draft_id)
        if draft:
            return draft.mapping_evidence
        return None

    def _get_draft_or_raise(self, db: Session, draft_id: int) -> CatalogEntryDraft:
        """Get draft by ID or raise ValueError."""
        draft = self.repository.find_by_id(db, draft_id)
        if not draft:
            raise ValueError(f"Draft not found: {draft_id}")
        if draft.status != DraftStatus.PENDING:
            raise ValueError(f"Draft {draft_id} is not in PENDING status: {draft.status}")
        return draft

    def discard(self, db: Session, draft_id: int) -> CatalogEntryDraft:
        """Discard a draft (change status to DISCARDED)."""
        draft = self._get_draft_or_raise(db, draft_id)
        draft.status = DraftStatus.DISCARDED
        return self.repository.update(db, draft)

    def publish(self, db: Session, draft_id: int) -> CatalogEntry:
        """Publish draft to catalog entry."""
        if not self.catalog_entry_service:
            raise ValueError("CatalogEntryService not configured for publish")

        draft = self._get_draft_or_raise(db, draft_id)

        # Create catalog entry from draft
        catalog_entry = CatalogEntry(
            title=draft.title,
            description=draft.description,
            issued=draft.issued,
            modified=draft.modified,
            publisher=draft.publisher,
            keyword=draft.keyword,
            theme=draft.theme,
            landing_page=draft.landing_page,
            access_url=draft.access_url,
            latest_snapshot_id=draft.snapshot_id,
        )

        saved_entry = self.catalog_entry_service.create_catalog_entry(db, catalog_entry)

        # Update draft status
        draft.status = DraftStatus.PUBLISHED
        self.repository.update(db, draft)

        return saved_entry
