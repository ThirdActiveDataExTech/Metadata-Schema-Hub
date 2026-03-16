"""Business logic for CatalogEntryDraft."""

from __future__ import annotations

from typing import Any

from active_metadata import CatalogEntryDraftBase, convert_field_types
from active_metadata.models import DraftStatus
from sqlmodel import Session

from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_entry_draft.exceptions import (
    DraftFieldNotEditableError,
    DraftMetadataSchemaNotFoundError,
    DraftNotFoundError,
    DraftNotPendingError,
)
from app.src.catalog_entry_draft.model import (
    CatalogEntryDraft,
    CatalogEntryDraftCreate,
    DecidedMapping,
    DraftFieldUpdate,
    MappingCandidate,
    MappingEvidence,
)
from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository
from app.src.column_relation.model import ColumnRelation
from app.src.events import (
    DiscardCompleted,
    EventBus,
    PublishCompleted,
)
from app.src.metadata_entry.model import MetadataEntry


class CatalogEntryDraftService:
    """CatalogEntryDraft service.

    Uses EventBus for lineage tracking - publishes domain events,
    LineageEventHandler subscribes and converts to lineage events.
    """

    def __init__(
        self,
        repository: CatalogEntryDraftRepository,
        event_bus: EventBus,
        catalog_entry_service: CatalogEntryService,
    ):
        """Initialize with repository, event bus, and catalog entry service."""
        self.repository = repository
        self.event_bus = event_bus
        self.catalog_entry_service = catalog_entry_service

    def build_mapping_with_evidence(
        self,
        metadata_entries: list[MetadataEntry],
        relations: list[ColumnRelation],
        top_k: int = 3,
    ) -> dict[str, MappingEvidence]:
        """Build mapping evidence per catalog column (3-key structure).

        Returns:
            Evidence map: catalog_column -> MappingEvidence
            - candidates: top-k candidates from column_relation
            - recommended: algorithm's top-1 recommendation
            - decided: initial value = recommended (editable by user)
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

        # Build evidence (candidates + recommended + decided)
        evidence_map: dict[str, MappingEvidence] = {}
        for catalog_column, candidates in column_candidates.items():
            if candidates:
                recommended = candidates[0]
                evidence_map[catalog_column] = MappingEvidence(
                    candidates=candidates[:top_k],
                    recommended=recommended,
                    decided=DecidedMapping(
                        metadata_column=recommended.metadata_column,
                        correlation=recommended.correlation,
                        value=recommended.value,
                    ),
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
        mapped_fields = {col: ev.decided.value for col, ev in evidence_map.items()}

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

    def get_draft(self, db: Session, draft_id: int) -> CatalogEntryDraft | None:
        """Get draft by ID."""
        return self.repository.find_by_id(db, draft_id)

    def get_drafts_by_snapshot(
        self, db: Session, snapshot_id: str, limit: int = 100, offset: int = 0
    ) -> list[CatalogEntryDraft]:
        """Get all drafts for a snapshot."""
        return self.repository.find_by_snapshot_id(db, snapshot_id, limit, offset)

    def get_all_drafts(self, db: Session, limit: int = 100, offset: int = 0) -> list[CatalogEntryDraft]:
        """Get all drafts with pagination."""
        return self.repository.find_all(db, limit, offset)

    def get_mapping_evidence(self, db: Session, draft_id: int) -> dict[str, Any] | None:
        """Get mapping evidence for a draft."""
        draft = self.get_draft(db, draft_id)
        if draft:
            return draft.mapping_evidence
        return None

    def _get_draft_or_raise(self, db: Session, draft_id: int) -> CatalogEntryDraft:
        """Get draft by ID or raise DraftNotFoundError."""
        draft = self.repository.find_by_id(db, draft_id)
        if not draft:
            raise DraftNotFoundError(draft_id)
        return draft

    def _ensure_pending(self, draft: CatalogEntryDraft) -> None:
        """Ensure draft is in PENDING status or raise DraftNotPendingError."""
        if draft.status != DraftStatus.PENDING:
            raise DraftNotPendingError(draft.id, draft.status)  # type: ignore[arg-type]

    def discard(self, db: Session, draft_id: int) -> CatalogEntryDraft:
        """Discard a draft (change status to DISCARDED)."""
        draft = self._get_draft_or_raise(db, draft_id)

        if draft.status != DraftStatus.PENDING:
            raise DraftNotPendingError(draft.id, draft.status)  # type: ignore[arg-type]

        draft.status = DraftStatus.DISCARDED
        updated_draft = self.repository.update(db, draft)
        db.flush()
        self.event_bus.publish(DiscardCompleted(draft_id=draft_id))
        return updated_draft

    def publish(self, db: Session, draft_id: int) -> CatalogEntry:
        """Publish draft to catalog entry."""
        # TODO: catalog_entry service 쪽으로 로직 이동
        draft = self._get_draft_or_raise(db, draft_id)

        if draft.status != DraftStatus.PENDING:
            raise DraftNotPendingError(draft.id, draft.status)  # type: ignore[arg-type]

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

        draft.status = DraftStatus.PUBLISHED
        self.repository.update(db, draft)
        db.flush()

        self.event_bus.publish(
            PublishCompleted(
                draft_id=draft_id,
                catalog_entry_id=saved_entry.id,  # type: ignore[arg-type]
            )
        )
        return saved_entry

    def update_draft_fields(
        self,
        db: Session,
        draft: CatalogEntryDraft,
        updates: list[DraftFieldUpdate],
        metadata_entries: list[MetadataEntry],
    ) -> CatalogEntryDraft:
        """Update draft fields by selecting from metadata_entries.

        Args:
            db: Database session
            draft: Draft to update (must be in PENDING status)
            updates: List of field updates (catalog_field, metadata_schema)
            metadata_entries: Available metadata entries for the draft's snapshot

        Returns:
            Updated draft with modified fields and evidence.decided

        Raises:
            DraftNotPendingError: If draft is not in PENDING status
            DraftFieldNotEditableError: If catalog_field is not editable
            DraftMetadataSchemaNotFoundError: If metadata_schema doesn't exist
        """
        if draft.status != DraftStatus.PENDING:
            raise DraftNotPendingError(draft.id, draft.status)  # type: ignore[arg-type]

        # Build metadata lookup dict
        metadata_dict = {e.metadata_schema: e.value for e in metadata_entries}

        # TODO: catalog_entry.get_content_fields()
        editable_fields = {
            "title",
            "description",
            "issued",
            "modified",
            "publisher",
            "keyword",
            "theme",
            "landing_page",
            "access_url",
        }

        for update in updates:
            # Validate catalog_field
            if update.catalog_field not in editable_fields:
                raise DraftFieldNotEditableError(update.catalog_field)

            # Validate metadata_schema exists
            if update.metadata_schema not in metadata_dict:
                raise DraftMetadataSchemaNotFoundError(update.metadata_schema)

            value = metadata_dict[update.metadata_schema]

            # Convert field type (str -> date, str -> list[str])
            typed_value = convert_field_types(
                {update.catalog_field: value},
                list_fields=CatalogEntryDraftBase.get_list_fields(),
                date_fields=CatalogEntryDraftBase.get_date_fields(),
            ).get(update.catalog_field, value)

            # Update draft field
            setattr(draft, update.catalog_field, typed_value)

            # Update or create evidence.decided
            evidence = draft.mapping_evidence.get(update.catalog_field)
            if evidence:
                # Check if out of candidates
                candidate_schemas = [c["metadata_column"] for c in evidence.get("candidates", [])]
                is_out_of_candidates = update.metadata_schema not in candidate_schemas

                # Find correlation from candidates
                correlation = None
                for c in evidence.get("candidates", []):
                    if c["metadata_column"] == update.metadata_schema:
                        correlation = c["correlation"]
                        break

                evidence["decided"] = {
                    "metadata_column": update.metadata_schema,
                    "correlation": correlation,
                    "value": value,
                    "out_of_candidates": is_out_of_candidates,
                }
            else:
                # Create new evidence for field that had no candidates
                decided = {
                    "metadata_column": update.metadata_schema,
                    "correlation": None,
                    "value": value,
                    "out_of_candidates": True,  # No candidates existed
                }
                draft.mapping_evidence[update.catalog_field] = {
                    "candidates": [],
                    "recommended": None,
                    "decided": decided,
                }

        return self.repository.update(db, draft)
