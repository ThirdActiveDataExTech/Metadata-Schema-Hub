"""Integration tests for CatalogEntryDraftRepository."""

import pytest
from sqlmodel import Session

from active_metadata.models import DraftStatus
from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository
from tests.constants import NONEXISTENT_ID, NONEXISTENT_IDENTIFIER, SNAPSHOT_ID_VALID, TEST_MAPPING_VERSION


class TestSave:
    """Tests for save method."""

    def test_save_new_draft(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
    ) -> None:
        """Should save new draft and return with ID."""
        draft = CatalogEntryDraft(
            snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version=TEST_MAPPING_VERSION,
            status=DraftStatus.PENDING,
            title="New Draft",
            mapping_evidence={},
        )

        result = catalog_entry_draft_repository.save(db, draft)

        assert result.id is not None
        assert result.title == "New Draft"


class TestFindById:
    """Tests for find_by_id method."""

    def test_find_existing(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return draft when found."""
        draft = sample_catalog_entry_drafts[0]
        result = catalog_entry_draft_repository.find_by_id(db, draft.id)

        assert result is not None
        assert result.id == draft.id

    def test_find_nonexistent(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
    ) -> None:
        """Should return None when not found."""
        result = catalog_entry_draft_repository.find_by_id(db, NONEXISTENT_ID)
        assert result is None


class TestFindBySnapshotId:
    """Tests for find_by_snapshot_id method."""

    def test_find_by_snapshot_id(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return drafts for snapshot."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(db, SNAPSHOT_ID_VALID)
        expected_count = sum(
            1 for d in sample_catalog_entry_drafts if d.snapshot_id == SNAPSHOT_ID_VALID
        )
        assert len(result) == expected_count

    def test_find_with_pagination(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should apply pagination."""
        limit = 1
        result = catalog_entry_draft_repository.find_by_snapshot_id(
            db, SNAPSHOT_ID_VALID, limit=limit
        )
        assert len(result) == limit

    def test_find_nonexistent(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
    ) -> None:
        """Should return empty list."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(db, NONEXISTENT_IDENTIFIER)
        assert result == []


class TestFindAll:
    """Tests for find_all method."""

    def test_find_all(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return all drafts."""
        result = catalog_entry_draft_repository.find_all(db)
        assert len(result) == len(sample_catalog_entry_drafts)

    def test_find_all_with_pagination(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should respect pagination."""
        limit = 2
        result = catalog_entry_draft_repository.find_all(db, limit=limit, offset=1)
        assert len(result) == limit


class TestUpdate:
    """Tests for update method."""

    def test_update_draft(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should update draft."""
        draft = sample_catalog_entry_drafts[0]
        draft.title = "Updated Title"
        draft.status = DraftStatus.PUBLISHED

        result = catalog_entry_draft_repository.update(db, draft)

        assert result.title == "Updated Title"
        assert result.status == DraftStatus.PUBLISHED

    def test_update_mapping_evidence(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should update JSONB field (mapping_evidence)."""
        draft = sample_catalog_entry_drafts[0]
        new_evidence = {
            "title": [{"schema": "dct:title", "score": 0.99}],
            "description": [{"schema": "dct:description", "score": 0.95}],
        }
        draft.mapping_evidence = new_evidence

        result = catalog_entry_draft_repository.update(db, draft)

        # Verify JSONB was updated
        refreshed = catalog_entry_draft_repository.find_by_id(db, draft.id)
        assert refreshed.mapping_evidence == new_evidence
