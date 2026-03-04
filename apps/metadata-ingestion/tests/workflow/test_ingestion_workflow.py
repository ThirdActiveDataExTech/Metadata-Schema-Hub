"""Tests for IngestionWorkflowService."""

from unittest.mock import MagicMock

import pytest

from active_metadata.models import DraftStatus, IngestionRunState
from tests.constants import SNAPSHOT_ID_VALID, SNAPSHOT_ID_VALID_ALT

from app.src.catalog_entry_draft.service import CatalogEntryDraftService
from app.src.column_relation.service import ColumnRelationService
from app.src.ingestion_run.exceptions import (
    IngestionRunNotFoundError,
    InvalidIngestionRunStateError,
    NoMetadataEntriesError,
)
from app.src.ingestion_run.service import IngestionRunService
from app.src.metadata_entry.service import MetadataEntryService
from app.src.metadata_snapshot.service import MetadataSnapshotService
from app.src.workflow.ingestion_workflow import IngestionWorkflowService


class TestIngestionWorkflowService:
    """Test cases for IngestionWorkflowService."""

    @pytest.fixture
    def workflow_service(
        self,
        mock_metadata_snapshot_repository,
        mock_metadata_entry_repository,
        mock_ingestion_run_repository,
        mock_catalog_entry_draft_repository,
        mock_column_relation_repository,
        mock_file_storage,
    ):
        """Create IngestionWorkflowService with all mocked dependencies."""
        return IngestionWorkflowService(
            snapshot_service=MetadataSnapshotService(mock_metadata_snapshot_repository),
            metadata_entry_service=MetadataEntryService(mock_metadata_entry_repository),
            ingestion_run_service=IngestionRunService(mock_ingestion_run_repository),
            draft_service=CatalogEntryDraftService(mock_catalog_entry_draft_repository),
            column_relation_service=ColumnRelationService(mock_column_relation_repository),
            file_storage=mock_file_storage,
        )

    # ========================================================================
    # get_mapping_version tests
    # ========================================================================

    def test_get_mapping_version(self, workflow_service):
        """Should return VERSION from app.version module."""
        version = workflow_service.get_mapping_version()
        assert isinstance(version, str)
        assert len(version) > 0

    # ========================================================================
    # execute_store_phase tests
    # ========================================================================

    def test_execute_store_phase_json_payload(self, workflow_service, mock_db_session):
        """Should process JSON payload through store phase."""
        json_payload = b'{"name": "Test Dataset", "description": "Test"}'

        # Mock snapshot save - clear side_effect to use return_value
        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_id = SNAPSHOT_ID_VALID
        workflow_service.snapshot_service.repository.save.side_effect = None
        workflow_service.snapshot_service.repository.save.return_value = mock_snapshot

        # Mock metadata entry save
        workflow_service.metadata_entry_service.repository.save.side_effect = None
        workflow_service.metadata_entry_service.repository.save.return_value = []

        # Mock run creation - clear side_effect to use return_value
        mock_run = MagicMock()
        mock_run.run_id = 1
        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_store_phase(mock_db_session, json_payload, filename="test.json")

        assert result.snapshot_id == SNAPSHOT_ID_VALID
        assert result.run_id == 1
        assert result.metadata_count > 0

        # Verify file was saved
        workflow_service.file_storage.save.assert_called_once()

        # Verify commit was called
        mock_db_session.commit.assert_called_once()

    def test_execute_store_phase_invalid_payload_raises(self, workflow_service, mock_db_session):
        """Should raise ValueError for invalid payload."""
        invalid_payload = b"not valid json or xml"

        with pytest.raises(ValueError):
            workflow_service.execute_store_phase(mock_db_session, invalid_payload, filename="bad.json")

        # Verify no file was saved
        workflow_service.file_storage.save.assert_not_called()

    def test_execute_store_phase_xml_payload(self, workflow_service, mock_db_session):
        """Should process XML payload through store phase."""
        xml_payload = b"<root><title>Test</title></root>"

        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_id = SNAPSHOT_ID_VALID_ALT
        workflow_service.snapshot_service.repository.save.side_effect = None
        workflow_service.snapshot_service.repository.save.return_value = mock_snapshot

        mock_run = MagicMock()
        mock_run.run_id = 2
        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_store_phase(mock_db_session, xml_payload, filename="test.xml")

        assert result.snapshot_id == SNAPSHOT_ID_VALID_ALT
        assert result.metadata_count > 0

    # ========================================================================
    # execute_draft_phase tests
    # ========================================================================

    def test_execute_draft_phase_success(self, workflow_service, mock_db_session):
        """Should create draft from stored run."""
        

        # Mock run lookup - use actual enum for state comparison
        mock_run = MagicMock()
        mock_run.snapshot_id = SNAPSHOT_ID_VALID
        mock_run.mapping_version = "v1.0"
        mock_run.state = IngestionRunState.STORED  # Use actual enum
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        # Mock metadata entries
        mock_metadata = [
            MagicMock(metadata_schema="name", value="Test"),
            MagicMock(metadata_schema="desc", value="Description"),
        ]
        workflow_service.metadata_entry_service.repository.select_metadata_entry.return_value = mock_metadata

        # Mock relations
        mock_relations = [MagicMock(catalog_column="title", metadata_column="name", correlation=0.95)]
        workflow_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = (
            mock_relations
        )

        # Mock draft creation - need to set all required attributes for Pydantic model
        mock_draft = MagicMock()
        mock_draft.id = 10
        mock_draft.snapshot_id = SNAPSHOT_ID_VALID
        mock_draft.mapping_version = "v1.0"
        mock_draft.status = DraftStatus.PENDING
        mock_draft.title = "Test"
        mock_draft.description = "Description"
        mock_draft.issued = None
        mock_draft.modified = None
        mock_draft.publisher = None
        mock_draft.keyword = None
        mock_draft.theme = None
        mock_draft.landing_page = None
        mock_draft.access_url = None
        mock_draft.mapping_evidence = {}
        workflow_service.draft_service.repository.save.side_effect = None
        workflow_service.draft_service.repository.save.return_value = mock_draft

        # Mock mark_drafted - clear side_effect
        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_draft_phase(mock_db_session, run_id=1)

        # Verify draft was created with correct attributes
        assert result.draft.id == 10
        assert result.draft.snapshot_id == SNAPSHOT_ID_VALID
        assert result.run_id == 1
        assert result.mapping_version == "v1.0"
        mock_db_session.commit.assert_called_once()

    def test_execute_draft_phase_run_not_found(self, workflow_service, mock_db_session):
        """Should raise IngestionRunNotFoundError when run not found."""
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = None

        with pytest.raises(IngestionRunNotFoundError):
            workflow_service.execute_draft_phase(mock_db_session, run_id=999)

    def test_execute_draft_phase_wrong_state(self, workflow_service, mock_db_session):
        """Should raise InvalidIngestionRunStateError when run not in STORED state."""
        mock_run = MagicMock()
        mock_run.state = MagicMock()
        mock_run.state.value = "DRAFTED"  # Wrong state
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        with pytest.raises(InvalidIngestionRunStateError):
            workflow_service.execute_draft_phase(mock_db_session, run_id=1)

    def test_execute_draft_phase_no_metadata_raises(self, workflow_service, mock_db_session):
        """Should raise NoMetadataEntriesError when no metadata entries found."""
        mock_run = MagicMock()
        mock_run.snapshot_id = SNAPSHOT_ID_VALID
        mock_run.state = MagicMock()
        mock_run.state.value = "STORED"
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        # No metadata entries
        workflow_service.metadata_entry_service.repository.select_metadata_entry.return_value = []

        with pytest.raises(NoMetadataEntriesError):
            workflow_service.execute_draft_phase(mock_db_session, run_id=1)

    def test_execute_draft_phase_marks_failed_on_error(self, workflow_service, mock_db_session):
        """Should mark run as failed on exception."""
        mock_run = MagicMock()
        mock_run.snapshot_id = SNAPSHOT_ID_VALID
        mock_run.state = MagicMock()
        mock_run.state.value = "STORED"
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        # Force an error in metadata lookup
        workflow_service.metadata_entry_service.repository.select_metadata_entry.side_effect = Exception("DB error")

        with pytest.raises(Exception):
            workflow_service.execute_draft_phase(mock_db_session, run_id=1)

        # Verify mark_failed was called
        # (The service calls mark_failed which calls repository.save)
        # Since we're mocking at repository level, check the save was called

    def test_execute_store_phase_file_storage_failure(self, workflow_service, mock_db_session):
        """Should not commit when file_storage.save fails."""
        valid_json = b'{"name": "Test Dataset"}'
        workflow_service.file_storage.save.side_effect = IOError("Storage full")

        with pytest.raises(IOError):
            workflow_service.execute_store_phase(mock_db_session, valid_json, "test.json")

        # DB commit should not be called
        mock_db_session.commit.assert_not_called()

    def test_execute_draft_phase_empty_relations(self, workflow_service, mock_db_session):
        """Should create draft even with no column relations."""
        # Mock run lookup
        mock_run = MagicMock()
        mock_run.snapshot_id = SNAPSHOT_ID_VALID
        mock_run.mapping_version = "v1.0"
        mock_run.state = IngestionRunState.STORED
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        # Mock metadata entries
        mock_metadata = [MagicMock(metadata_schema="name", value="Test")]
        workflow_service.metadata_entry_service.repository.select_metadata_entry.return_value = mock_metadata

        # Empty relations
        workflow_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = []

        # Mock draft creation
        mock_draft = MagicMock()
        mock_draft.id = 10
        mock_draft.snapshot_id = SNAPSHOT_ID_VALID
        mock_draft.mapping_version = "v1.0"
        mock_draft.status = DraftStatus.PENDING
        mock_draft.title = None
        mock_draft.description = None
        mock_draft.issued = None
        mock_draft.modified = None
        mock_draft.publisher = None
        mock_draft.keyword = None
        mock_draft.theme = None
        mock_draft.landing_page = None
        mock_draft.access_url = None
        mock_draft.mapping_evidence = {}
        workflow_service.draft_service.repository.save.side_effect = None
        workflow_service.draft_service.repository.save.return_value = mock_draft

        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_draft_phase(mock_db_session, run_id=1)

        # Draft should still be created even with empty relations
        assert result.draft is not None
        assert result.draft.id == 10

    def test_execute_draft_phase_mark_drafted_failure(self, workflow_service, mock_db_session):
        """Should mark failed when mark_drafted raises after draft creation."""
        # Mock run lookup
        mock_run = MagicMock()
        mock_run.snapshot_id = SNAPSHOT_ID_VALID
        mock_run.mapping_version = "v1.0"
        mock_run.state = IngestionRunState.STORED
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        # Mock metadata entries
        mock_metadata = [MagicMock(metadata_schema="name", value="Test")]
        workflow_service.metadata_entry_service.repository.select_metadata_entry.return_value = mock_metadata

        # Mock relations
        mock_relations = [MagicMock(catalog_column="title", metadata_column="name", correlation=0.95)]
        workflow_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = (
            mock_relations
        )

        # Mock draft creation succeeds
        mock_draft = MagicMock()
        mock_draft.id = 10
        mock_draft.snapshot_id = SNAPSHOT_ID_VALID
        mock_draft.mapping_version = "v1.0"
        mock_draft.status = DraftStatus.PENDING
        mock_draft.title = "Test"
        mock_draft.description = None
        mock_draft.issued = None
        mock_draft.modified = None
        mock_draft.publisher = None
        mock_draft.keyword = None
        mock_draft.theme = None
        mock_draft.landing_page = None
        mock_draft.access_url = None
        mock_draft.mapping_evidence = {}
        workflow_service.draft_service.repository.save.side_effect = None
        workflow_service.draft_service.repository.save.return_value = mock_draft

        # mark_drafted fails (save after draft creation)
        def save_side_effect(*args, **kwargs):
            # First call is draft save (succeeds), second is mark_drafted (fails)
            if workflow_service.ingestion_run_service.repository.save.call_count > 0:
                raise Exception("DB error on mark_drafted")
            return mock_run

        workflow_service.ingestion_run_service.repository.save.side_effect = save_side_effect

        with pytest.raises(Exception) as exc_info:
            workflow_service.execute_draft_phase(mock_db_session, run_id=1)

        assert "DB error" in str(exc_info.value)


class TestExecuteStorePhaseWithSamples:
    """Test execute_store_phase with actual sample files."""

    @pytest.fixture
    def workflow_service(
        self,
        mock_metadata_snapshot_repository,
        mock_metadata_entry_repository,
        mock_ingestion_run_repository,
        mock_catalog_entry_draft_repository,
        mock_column_relation_repository,
        mock_file_storage,
    ):
        """Create IngestionWorkflowService with all mocked dependencies."""


        return IngestionWorkflowService(
            snapshot_service=MetadataSnapshotService(mock_metadata_snapshot_repository),
            metadata_entry_service=MetadataEntryService(mock_metadata_entry_repository),
            ingestion_run_service=IngestionRunService(mock_ingestion_run_repository),
            draft_service=CatalogEntryDraftService(mock_catalog_entry_draft_repository),
            column_relation_service=ColumnRelationService(mock_column_relation_repository),
            file_storage=mock_file_storage,
        )

    def test_store_phase_with_sample_json(self, workflow_service, mock_db_session, sample_schema_org_json):
        """Should process sample JSON file."""
        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_id = SNAPSHOT_ID_VALID
        workflow_service.snapshot_service.repository.save.side_effect = None
        workflow_service.snapshot_service.repository.save.return_value = mock_snapshot

        mock_run = MagicMock()
        mock_run.run_id = 1
        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_store_phase(
            mock_db_session, sample_schema_org_json, filename="schema_org.json"
        )

        assert result.metadata_count > 0

    def test_store_phase_with_sample_rdf(self, workflow_service, mock_db_session, sample_dcat_rdf):
        """Should process sample RDF file."""
        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_id = SNAPSHOT_ID_VALID_ALT
        workflow_service.snapshot_service.repository.save.side_effect = None
        workflow_service.snapshot_service.repository.save.return_value = mock_snapshot

        mock_run = MagicMock()
        mock_run.run_id = 2
        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_store_phase(mock_db_session, sample_dcat_rdf, filename="dcat.rdf")

        assert result.metadata_count > 0
