"""Integration tests for CatalogEntryDraftRepository."""

import pytest
from sqlmodel import Session

from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository


class TestFindById:
    """Tests for find_by_id method."""

    def test_find_existing_draft(
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
        assert result.title == "Draft Title 1"

    def test_find_nonexistent_returns_none(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
    ) -> None:
        """Should return None for non-existent ID."""
        result = catalog_entry_draft_repository.find_by_id(db, 99999)
        assert result is None


class TestFindBySnapshotId:
    """Tests for find_by_snapshot_id method."""

    def test_find_by_snapshot_id(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return drafts for given snapshot_id."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(db, "snapshot-001")

        assert len(result) == 2
        titles = {d.title for d in result}
        assert titles == {"Draft Title 1", "Draft Title 2"}

    def test_find_by_snapshot_id_with_pagination(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should apply limit and offset."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(
            db, "snapshot-001", limit=1, offset=0
        )
        assert len(result) == 1

    def test_find_nonexistent_snapshot(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
    ) -> None:
        """Should return empty list for non-existent snapshot."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(db, "nonexistent")
        assert result == []

    def test_find_ordered_by_created_at_desc(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return drafts ordered by created_at descending."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(db, "snapshot-001")

        # Most recently created first
        assert result[0].created_at >= result[1].created_at


class TestFindAll:
    """Tests for find_all method."""

    def test_find_all_drafts(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return all drafts."""
        result = catalog_entry_draft_repository.find_all(db)
        assert len(result) == 3

    def test_find_all_with_limit(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should respect limit parameter."""
        result = catalog_entry_draft_repository.find_all(db, limit=2)
        assert len(result) == 2

    def test_find_all_with_offset(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should respect offset parameter."""
        all_drafts = catalog_entry_draft_repository.find_all(db)
        offset_result = catalog_entry_draft_repository.find_all(db, offset=1)

        assert len(offset_result) == 2
        assert offset_result[0].id != all_drafts[0].id

    def test_find_all_empty(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
    ) -> None:
        """Should return empty list when no drafts."""
        result = catalog_entry_draft_repository.find_all(db)
        assert result == []

    def test_find_all_ordered_by_created_at_desc(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return drafts ordered by created_at descending."""
        result = catalog_entry_draft_repository.find_all(db)

        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at
