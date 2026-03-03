"""Tests for CatalogEntryDraftService."""

from unittest.mock import MagicMock

from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_entry_draft.service import CatalogEntryDraftService


class TestGetDraft:
    """Tests for get_draft method."""

    def test_returns_draft_by_id(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry_draft: CatalogEntryDraft,
    ) -> None:
        """Should return draft when found by ID."""
        mock_catalog_entry_draft_repository.find_by_id.return_value = sample_catalog_entry_draft

        result = catalog_entry_draft_service.get_draft(mock_db, 1)

        assert result == sample_catalog_entry_draft
        mock_catalog_entry_draft_repository.find_by_id.assert_called_once_with(mock_db, 1)

    def test_returns_none_when_not_found(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return None when draft not found."""
        mock_catalog_entry_draft_repository.find_by_id.return_value = None

        result = catalog_entry_draft_service.get_draft(mock_db, 999)

        assert result is None


class TestGetDraftsBySnapshot:
    """Tests for get_drafts_by_snapshot method."""

    def test_returns_drafts_for_snapshot(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry_draft: CatalogEntryDraft,
    ) -> None:
        """Should return drafts for given snapshot ID."""
        drafts = [sample_catalog_entry_draft]
        mock_catalog_entry_draft_repository.find_by_snapshot_id.return_value = drafts

        result = catalog_entry_draft_service.get_drafts_by_snapshot(mock_db, "abc123def456")

        assert result == drafts
        mock_catalog_entry_draft_repository.find_by_snapshot_id.assert_called_once_with(
            mock_db, "abc123def456", 100, 0
        )

    def test_with_pagination_parameters(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should pass pagination parameters to repository."""
        mock_catalog_entry_draft_repository.find_by_snapshot_id.return_value = []

        catalog_entry_draft_service.get_drafts_by_snapshot(mock_db, "abc123", limit=50, offset=10)

        mock_catalog_entry_draft_repository.find_by_snapshot_id.assert_called_once_with(
            mock_db, "abc123", 50, 10
        )


class TestGetAllDrafts:
    """Tests for get_all_drafts method."""

    def test_returns_all_drafts(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry_draft: CatalogEntryDraft,
    ) -> None:
        """Should return all drafts with default pagination."""
        drafts = [sample_catalog_entry_draft]
        mock_catalog_entry_draft_repository.find_all.return_value = drafts

        result = catalog_entry_draft_service.get_all_drafts(mock_db)

        assert result == drafts
        mock_catalog_entry_draft_repository.find_all.assert_called_once_with(mock_db, 100, 0)

    def test_with_pagination_parameters(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should pass pagination parameters to repository."""
        mock_catalog_entry_draft_repository.find_all.return_value = []

        catalog_entry_draft_service.get_all_drafts(mock_db, limit=25, offset=50)

        mock_catalog_entry_draft_repository.find_all.assert_called_once_with(mock_db, 25, 50)

    def test_returns_empty_list_when_no_drafts(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty list when no drafts exist."""
        mock_catalog_entry_draft_repository.find_all.return_value = []

        result = catalog_entry_draft_service.get_all_drafts(mock_db)

        assert result == []

    def test_passes_negative_offset_to_repository(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should pass negative offset to repository (validation at DB/repository level)."""
        mock_catalog_entry_draft_repository.find_all.return_value = []

        catalog_entry_draft_service.get_all_drafts(mock_db, limit=10, offset=-1)

        # Service passes through; repository/DB handles validation
        mock_catalog_entry_draft_repository.find_all.assert_called_once_with(mock_db, 10, -1)


class TestGetMappingEvidence:
    """Tests for get_mapping_evidence method."""

    def test_returns_mapping_evidence(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry_draft: CatalogEntryDraft,
    ) -> None:
        """Should return mapping evidence for draft."""
        mock_catalog_entry_draft_repository.find_by_id.return_value = sample_catalog_entry_draft

        result = catalog_entry_draft_service.get_mapping_evidence(mock_db, 1)

        assert result is not None
        assert "title" in result
        assert result["title"][0]["score"] == 0.95

    def test_returns_none_when_draft_not_found(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return None when draft not found."""
        mock_catalog_entry_draft_repository.find_by_id.return_value = None

        result = catalog_entry_draft_service.get_mapping_evidence(mock_db, 999)

        assert result is None

    def test_returns_empty_dict_when_no_evidence(
        self,
        catalog_entry_draft_service: CatalogEntryDraftService,
        mock_catalog_entry_draft_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty dict when draft has no mapping evidence."""
        draft = CatalogEntryDraft(
            id=1,
            snapshot_id="abc123",
            mapping_version="v1.0",
            mapping_evidence={},
        )
        mock_catalog_entry_draft_repository.find_by_id.return_value = draft

        result = catalog_entry_draft_service.get_mapping_evidence(mock_db, 1)

        assert result == {}
