"""Tests for CatalogEntryDraftService."""

from unittest.mock import MagicMock

import pytest

from active_metadata.models import DraftStatus
from tests.constants import SNAPSHOT_ID_VALID, TEST_MAPPING_VERSION
from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_entry_draft.service import CatalogEntryDraftService
from app.src.column_relation.model import ColumnRelation
from app.src.metadata_entry.model import MetadataEntry
from app.src.catalog_entry.service import CatalogEntryService

class TestBuildMappingWithEvidence:
    """Test cases for build_mapping_with_evidence method."""

    @pytest.fixture
    def service(self, mock_catalog_entry_draft_repository, mock_event_bus):
        """Create service instance."""
        mock_catalog_service = MagicMock(spec=CatalogEntryService)
        return CatalogEntryDraftService(
            repository=mock_catalog_entry_draft_repository,
            event_bus=mock_event_bus,
            catalog_entry_service=mock_catalog_service,
        )

    @pytest.fixture
    def sample_metadata_entries(self):
        """Create sample MetadataEntry list."""
        return [
            MagicMock(spec=MetadataEntry, metadata_schema="name", value="Test Dataset"),
            MagicMock(spec=MetadataEntry, metadata_schema="description", value="Test Description"),
            MagicMock(spec=MetadataEntry, metadata_schema="keywords", value="test,data"),
            MagicMock(spec=MetadataEntry, metadata_schema="dateModified", value="2024-01-01"),
        ]

    @pytest.fixture
    def sample_relations(self):
        """Create sample ColumnRelation list."""
        return [
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95),
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="description", correlation=0.80),
            MagicMock(spec=ColumnRelation, catalog_column="description", metadata_column="description", correlation=0.90),
            MagicMock(spec=ColumnRelation, catalog_column="keyword", metadata_column="keywords", correlation=0.85),
            MagicMock(spec=ColumnRelation, catalog_column="modified", metadata_column="dateModified", correlation=0.88),
        ]

    def test_build_mapping_returns_evidence_map(self, service, sample_metadata_entries, sample_relations):
        """Should return dict mapping catalog columns to evidence."""
        result = service.build_mapping_with_evidence(sample_metadata_entries, sample_relations)

        assert isinstance(result, dict)
        assert "title" in result
        assert "description" in result
        assert "keyword" in result
        assert "modified" in result

    def test_build_mapping_selects_highest_correlation(self, service, sample_metadata_entries, sample_relations):
        """Should select highest correlation as selected value."""
        result = service.build_mapping_with_evidence(sample_metadata_entries, sample_relations)

        # title has two candidates: name (0.95) and description (0.80)
        assert result["title"].selected.metadata_column == "name"
        assert result["title"].selected.correlation == 0.95
        assert result["title"].selected.value == "Test Dataset"

    def test_build_mapping_includes_alternatives(self, service, sample_metadata_entries, sample_relations):
        """Should include alternatives in evidence."""
        result = service.build_mapping_with_evidence(sample_metadata_entries, sample_relations, top_k=3)

        # title has two candidates, so alternatives should have 1 item
        assert len(result["title"].alternatives) == 1
        assert result["title"].alternatives[0].metadata_column == "description"
        assert result["title"].alternatives[0].correlation == 0.80

    def test_build_mapping_respects_top_k(self, service):
        """Should limit alternatives to top_k - 1."""
        metadata_entries = [
            MagicMock(spec=MetadataEntry, metadata_schema=f"field{i}", value=f"value{i}") for i in range(5)
        ]
        relations = [
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column=f"field{i}", correlation=0.9 - i * 0.1)
            for i in range(5)
        ]

        result = service.build_mapping_with_evidence(metadata_entries, relations, top_k=3)

        # Should have 1 selected + 2 alternatives (top_k=3)
        assert len(result["title"].alternatives) == 2

    def test_build_mapping_no_matching_metadata(self, service):
        """Should return empty dict when no metadata matches relations."""
        metadata_entries = [MagicMock(spec=MetadataEntry, metadata_schema="unrelated", value="value")]
        relations = [MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95)]

        result = service.build_mapping_with_evidence(metadata_entries, relations)

        assert result == {}

    def test_build_mapping_empty_inputs(self, service):
        """Should handle empty inputs."""
        result = service.build_mapping_with_evidence([], [])
        assert result == {}


class TestCatalogEntryDraftService:
    """Test cases for CatalogEntryDraftService CRUD operations."""

    # ========================================================================
    # create_draft tests
    # ========================================================================

    def test_create_draft(self, catalog_entry_draft_service, mock_db_session):
        """Should create draft with mapping evidence."""
        metadata_entries = [
            MagicMock(spec=MetadataEntry, metadata_schema="name", value="Test Title"),
        ]
        relations = [
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95),
        ]

        catalog_entry_draft_service.repository.save.side_effect = lambda db, d: d

        result = catalog_entry_draft_service.create_draft(
            mock_db_session,
            snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version="v1.0",
            metadata_entries=metadata_entries,
            relations=relations,
        )

        assert isinstance(result, CatalogEntryDraft)
        assert result.snapshot_id == SNAPSHOT_ID_VALID
        assert result.mapping_version == "v1.0"
        catalog_entry_draft_service.repository.save.assert_called_once()

    # ========================================================================
    # get_draft tests
    # ========================================================================

    def test_get_draft_found(self, catalog_entry_draft_service, mock_db_session):
        """Should return draft when found."""
        expected = MagicMock(spec=CatalogEntryDraft)
        catalog_entry_draft_service.repository.find_by_id.return_value = expected

        result = catalog_entry_draft_service.get_draft(mock_db_session, 1)

        assert result == expected
        catalog_entry_draft_service.repository.find_by_id.assert_called_once_with(mock_db_session, 1)

    def test_get_draft_not_found(self, catalog_entry_draft_service, mock_db_session):
        """Should return None when not found."""
        catalog_entry_draft_service.repository.find_by_id.return_value = None

        result = catalog_entry_draft_service.get_draft(mock_db_session, 999)

        assert result is None

    # ========================================================================
    # get_drafts_by_snapshot tests
    # ========================================================================

    def test_get_drafts_by_snapshot(self, catalog_entry_draft_service, mock_db_session):
        """Should return drafts for snapshot."""
        expected = [MagicMock(), MagicMock()]
        catalog_entry_draft_service.repository.find_by_snapshot_id.return_value = expected

        result = catalog_entry_draft_service.get_drafts_by_snapshot(mock_db_session, SNAPSHOT_ID_VALID, limit=10, offset=0)

        assert result == expected
        catalog_entry_draft_service.repository.find_by_snapshot_id.assert_called_once_with(
            mock_db_session, SNAPSHOT_ID_VALID, 10, 0
        )

    # ========================================================================
    # get_all_drafts tests
    # ========================================================================

    def test_get_all_drafts(self, catalog_entry_draft_service, mock_db_session):
        """Should return all drafts with pagination."""
        expected = [MagicMock(), MagicMock()]
        catalog_entry_draft_service.repository.find_all.return_value = expected

        result = catalog_entry_draft_service.get_all_drafts(mock_db_session, limit=50, offset=10)

        assert result == expected
        catalog_entry_draft_service.repository.find_all.assert_called_once_with(mock_db_session, 50, 10)

    # ========================================================================
    # get_mapping_evidence tests
    # ========================================================================

    def test_get_mapping_evidence_found(self, catalog_entry_draft_service, mock_db_session):
        """Should return mapping_evidence from draft."""
        mock_draft = MagicMock(spec=CatalogEntryDraft)
        mock_draft.mapping_evidence = {"title": {"selected": {"value": "Test"}}}
        catalog_entry_draft_service.repository.find_by_id.return_value = mock_draft

        result = catalog_entry_draft_service.get_mapping_evidence(mock_db_session, 1)

        assert result == {"title": {"selected": {"value": "Test"}}}

    def test_get_mapping_evidence_not_found(self, catalog_entry_draft_service, mock_db_session):
        """Should return None when draft not found."""
        catalog_entry_draft_service.repository.find_by_id.return_value = None

        result = catalog_entry_draft_service.get_mapping_evidence(mock_db_session, 999)

        assert result is None

    # ========================================================================
    # discard tests
    # ========================================================================

    def test_discard_success(self, catalog_entry_draft_service, mock_db_session):
        """Should set status to DISCARDED."""
        mock_draft = MagicMock(spec=CatalogEntryDraft)
        mock_draft.status = DraftStatus.PENDING
        catalog_entry_draft_service.repository.find_by_id.return_value = mock_draft
        catalog_entry_draft_service.repository.update.side_effect = lambda db, d: d

        result = catalog_entry_draft_service.discard(mock_db_session, 1)

        assert result.status == DraftStatus.DISCARDED
        catalog_entry_draft_service.repository.update.assert_called_once()

    def test_discard_not_pending_raises(self, catalog_entry_draft_service, mock_db_session):
        """Should raise ValueError when not in PENDING status."""
        mock_draft = MagicMock(spec=CatalogEntryDraft)
        mock_draft.status = DraftStatus.PUBLISHED
        catalog_entry_draft_service.repository.find_by_id.return_value = mock_draft

        with pytest.raises(ValueError) as exc_info:
            catalog_entry_draft_service.discard(mock_db_session, 1)

        assert "PENDING" in str(exc_info.value)

    def test_discard_not_found_raises(self, catalog_entry_draft_service, mock_db_session):
        """Should raise ValueError when draft not found."""
        catalog_entry_draft_service.repository.find_by_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            catalog_entry_draft_service.discard(mock_db_session, 999)

        assert "not found" in str(exc_info.value)

    # ========================================================================
    # publish tests
    # ========================================================================

    def test_publish_success(
        self, mock_catalog_entry_draft_repository, mock_catalog_entry_repository, mock_event_bus, mock_db_session
    ):
        """Should create catalog entry and update draft status."""

        mock_catalog_service = MagicMock(spec=CatalogEntryService)
        mock_catalog_service.create_catalog_entry.side_effect = lambda db, e: e

        service = CatalogEntryDraftService(
            repository=mock_catalog_entry_draft_repository,
            event_bus=mock_event_bus,
            catalog_entry_service=mock_catalog_service,
        )

        mock_draft = MagicMock(spec=CatalogEntryDraft)
        mock_draft.status = DraftStatus.PENDING
        mock_draft.title = "Test Title"
        mock_draft.description = "Test Description"
        mock_draft.issued = None
        mock_draft.modified = None
        mock_draft.publisher = None
        mock_draft.keyword = None
        mock_draft.theme = None
        mock_draft.landing_page = None
        mock_draft.access_url = None
        mock_draft.snapshot_id = SNAPSHOT_ID_VALID
        service.repository.find_by_id.return_value = mock_draft
        service.repository.update.side_effect = lambda db, d: d

        result = service.publish(mock_db_session, 1)

        assert result.title == "Test Title"
        mock_catalog_service.create_catalog_entry.assert_called_once()
        assert mock_draft.status == DraftStatus.PUBLISHED

    def test_publish_not_pending_raises(
        self, mock_catalog_entry_draft_repository, mock_catalog_entry_repository, mock_event_bus, mock_db_session
    ):
        """Should raise when draft not in PENDING status."""

        mock_catalog_service = MagicMock(spec=CatalogEntryService)
        service = CatalogEntryDraftService(
            repository=mock_catalog_entry_draft_repository,
            event_bus=mock_event_bus,
            catalog_entry_service=mock_catalog_service,
        )

        mock_draft = MagicMock(spec=CatalogEntryDraft)
        mock_draft.status = DraftStatus.DISCARDED
        service.repository.find_by_id.return_value = mock_draft

        with pytest.raises(ValueError) as exc_info:
            service.publish(mock_db_session, 1)

        assert "PENDING" in str(exc_info.value)
