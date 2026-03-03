"""Integration tests for CatalogEntryDraftRepository."""

import pytest
from sqlmodel import Session

from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository
from tests.constants import NONEXISTENT_ID, NONEXISTENT_IDENTIFIER, SNAPSHOT_ID_VALID


class TestFindById:
    """Tests for find_by_id method."""

    def test_find_existing_draft(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return draft when found."""
        target_draft = sample_catalog_entry_drafts[0]
        result = catalog_entry_draft_repository.find_by_id(db, target_draft.id)

        assert result is not None
        assert result.id == target_draft.id
        assert result.title == target_draft.title

    def test_find_nonexistent_returns_none(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
    ) -> None:
        """Should return None for non-existent ID."""
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
        """Should return drafts for given snapshot_id."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(db, SNAPSHOT_ID_VALID)
        expected = [d for d in sample_catalog_entry_drafts if d.snapshot_id == SNAPSHOT_ID_VALID]
        assert len(result) == len(expected)
        titles = {d.title for d in result}
        expected_titles = {d.title for d in expected}
        assert titles == expected_titles

    def test_find_by_snapshot_id_with_pagination(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should apply limit and offset."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(
            db, SNAPSHOT_ID_VALID, limit=1, offset=0
        )
        assert len(result) == 1

    def test_find_nonexistent_snapshot(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
    ) -> None:
        """Should return empty list for non-existent snapshot."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(db, NONEXISTENT_IDENTIFIER)
        assert result == []

    def test_find_ordered_by_created_at_desc(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should return drafts ordered by created_at descending."""
        result = catalog_entry_draft_repository.find_by_snapshot_id(db, SNAPSHOT_ID_VALID)

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
        assert len(result) == len(sample_catalog_entry_drafts)

    def test_find_all_with_limit(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should respect limit parameter."""
        limit = 2
        result = catalog_entry_draft_repository.find_all(db, limit=limit)
        assert len(result) == limit

    def test_find_all_with_offset(
        self,
        db: Session,
        catalog_entry_draft_repository: CatalogEntryDraftRepository,
        sample_catalog_entry_drafts: list[CatalogEntryDraft],
    ) -> None:
        """Should respect offset parameter."""
        all_drafts = catalog_entry_draft_repository.find_all(db)
        offset = 1
        offset_result = catalog_entry_draft_repository.find_all(db, offset=offset)

        assert len(offset_result) == len(sample_catalog_entry_drafts) - offset
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
