"""Tests for IngestionWorkflowService."""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from active_metadata.models import IngestionRunState
from tests.constants import NONEXISTENT_UUID, SNAPSHOT_ID_VALID, SNAPSHOT_ID_VALID_ALT, TEST_RUN_UUID_1, TEST_RUN_UUID_2

from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_entry_draft.service import CatalogEntryDraftService
from app.src.catalog_merge.model import CatalogMerge
from app.src.catalog_merge.service import CatalogMergeService
from app.src.column_relation.service import ColumnRelationService
from app.src.ingestion_run.exceptions import (
    IngestionRunNotFoundError,
    InvalidIngestionRunStateError,
    NoMetadataEntriesError,
)
from app.src.ingestion_run.model import IngestionRun
from app.src.ingestion_run.service import IngestionRunService
from app.src.metadata_entry.service import MetadataEntryService
from app.src.metadata_snapshot.service import MetadataSnapshotService
from app.src.workflow.ingestion_workflow import IngestionWorkflowService


class TestIngestionWorkflowService:
    """Test cases for IngestionWorkflowService."""

    @pytest.fixture
    def mock_catalog_merge_service(self):
        """Create mock CatalogMergeService."""
        return MagicMock(spec=CatalogMergeService)

    @pytest.fixture
    def mock_catalog_entry_service(self):
        """Create mock CatalogEntryService."""
        return MagicMock(spec=CatalogEntryService)

    @pytest.fixture
    def workflow_service(
        self,
        mock_metadata_snapshot_repository,
        mock_metadata_entry_repository,
        mock_ingestion_run_repository,
        mock_catalog_entry_draft_repository,
        mock_column_relation_repository,
        mock_file_storage,
        mock_event_bus,
        mock_catalog_merge_service,
        mock_catalog_entry_service,
    ):
        """Create IngestionWorkflowService with all mocked dependencies."""
        return IngestionWorkflowService(
            snapshot_service=MetadataSnapshotService(mock_metadata_snapshot_repository),
            metadata_entry_service=MetadataEntryService(mock_metadata_entry_repository),
            ingestion_run_service=IngestionRunService(mock_ingestion_run_repository),
            draft_service=CatalogEntryDraftService(
                mock_catalog_entry_draft_repository, mock_event_bus, mock_catalog_entry_service
            ),
            column_relation_service=ColumnRelationService(mock_column_relation_repository),
            file_storage=mock_file_storage,
            event_bus=mock_event_bus,
            catalog_merge_service=mock_catalog_merge_service,
            catalog_entry_service=mock_catalog_entry_service,
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

        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_id = SNAPSHOT_ID_VALID
        workflow_service.snapshot_service.repository.save.side_effect = None
        workflow_service.snapshot_service.repository.save.return_value = mock_snapshot

        workflow_service.metadata_entry_service.repository.save.side_effect = None
        workflow_service.metadata_entry_service.repository.save.return_value = []

        mock_run = MagicMock()
        mock_run.run_id = TEST_RUN_UUID_1
        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_store_phase(mock_db_session, json_payload, filename="test.json")

        assert result.snapshot_id == SNAPSHOT_ID_VALID
        assert isinstance(result.run_id, UUID)
        assert result.metadata_count > 0
        workflow_service.file_storage.save.assert_called_once()
        mock_db_session.flush.assert_called()

    def test_execute_store_phase_invalid_payload_raises(self, workflow_service, mock_db_session):
        """Should raise ValueError for invalid payload."""
        invalid_payload = b"not valid json or xml"

        with pytest.raises(ValueError):
            workflow_service.execute_store_phase(mock_db_session, invalid_payload, filename="bad.json")

        workflow_service.file_storage.save.assert_not_called()

    def test_execute_store_phase_xml_payload(self, workflow_service, mock_db_session):
        """Should process XML payload through store phase."""
        xml_payload = b"<root><title>Test</title></root>"

        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_id = SNAPSHOT_ID_VALID_ALT
        workflow_service.snapshot_service.repository.save.side_effect = None
        workflow_service.snapshot_service.repository.save.return_value = mock_snapshot

        mock_run = MagicMock()
        mock_run.run_id = TEST_RUN_UUID_2
        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_store_phase(mock_db_session, xml_payload, filename="test.xml")

        assert result.snapshot_id == SNAPSHOT_ID_VALID_ALT
        assert isinstance(result.run_id, UUID)
        assert result.metadata_count > 0

    def test_execute_store_phase_file_storage_failure(self, workflow_service, mock_db_session):
        """Should not flush when file_storage.save fails."""
        valid_json = b'{"name": "Test Dataset"}'
        workflow_service.file_storage.save.side_effect = IOError("Storage full")

        with pytest.raises(IOError):
            workflow_service.execute_store_phase(mock_db_session, valid_json, "test.json")

        mock_db_session.flush.assert_not_called()

    # ========================================================================
    # execute_draft_phase tests
    # ========================================================================

    def test_execute_draft_phase_success(self, workflow_service, mock_db_session):
        """Should create draft from stored run."""
        mock_run = IngestionRun(
            run_id=TEST_RUN_UUID_1, snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version="v1.0", state=IngestionRunState.STORED,
        )
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        mock_metadata = [
            MagicMock(metadata_schema="name", value="Test"),
            MagicMock(metadata_schema="desc", value="Description"),
        ]
        workflow_service.metadata_entry_service.repository.select_metadata_entry.return_value = mock_metadata

        mock_relations = [MagicMock(catalog_column="title", metadata_column="name", correlation=0.95)]
        workflow_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = (
            mock_relations
        )

        mock_draft = CatalogEntryDraft(
            id=10, snapshot_id=SNAPSHOT_ID_VALID, mapping_version="v1.0",
            title="Test", description="Description",
        )
        workflow_service.draft_service.repository.save.side_effect = None
        workflow_service.draft_service.repository.save.return_value = mock_draft

        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_draft_phase(mock_db_session, run_id=TEST_RUN_UUID_1)

        assert result.draft.id == 10
        assert result.draft.snapshot_id == SNAPSHOT_ID_VALID
        assert result.mapping_version == "v1.0"
        mock_db_session.flush.assert_called()

    def test_execute_draft_phase_run_not_found(self, workflow_service, mock_db_session):
        """Should raise IngestionRunNotFoundError when run not found."""
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = None

        with pytest.raises(IngestionRunNotFoundError):
            workflow_service.execute_draft_phase(mock_db_session, run_id=NONEXISTENT_UUID)

    def test_execute_draft_phase_wrong_state(self, workflow_service, mock_db_session):
        """Should raise InvalidIngestionRunStateError when run not in STORED state."""
        mock_run = IngestionRun(
            run_id=TEST_RUN_UUID_1, snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version="v1.0", state=IngestionRunState.DRAFTED,
        )
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        with pytest.raises(InvalidIngestionRunStateError):
            workflow_service.execute_draft_phase(mock_db_session, run_id=TEST_RUN_UUID_1)

    def test_execute_draft_phase_no_metadata_raises(self, workflow_service, mock_db_session):
        """Should raise NoMetadataEntriesError when no metadata entries found."""
        mock_run = IngestionRun(
            run_id=TEST_RUN_UUID_1, snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version="v1.0", state=IngestionRunState.STORED,
        )
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        workflow_service.metadata_entry_service.repository.select_metadata_entry.return_value = []

        with pytest.raises(NoMetadataEntriesError):
            workflow_service.execute_draft_phase(mock_db_session, run_id=TEST_RUN_UUID_1)

    def test_execute_draft_phase_marks_failed_on_error(self, workflow_service, mock_db_session):
        """Should mark run as failed on exception."""
        mock_run = IngestionRun(
            run_id=TEST_RUN_UUID_1, snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version="v1.0", state=IngestionRunState.STORED,
        )
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        workflow_service.metadata_entry_service.repository.select_metadata_entry.side_effect = Exception("DB error")

        with pytest.raises(Exception):
            workflow_service.execute_draft_phase(mock_db_session, run_id=TEST_RUN_UUID_1)

        # mark_failed calls repository.save internally
        workflow_service.ingestion_run_service.repository.save.assert_called()

    def test_execute_draft_phase_empty_relations(self, workflow_service, mock_db_session):
        """Should create draft even with no column relations."""
        mock_run = IngestionRun(
            run_id=TEST_RUN_UUID_1, snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version="v1.0", state=IngestionRunState.STORED,
        )
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        mock_metadata = [MagicMock(metadata_schema="name", value="Test")]
        workflow_service.metadata_entry_service.repository.select_metadata_entry.return_value = mock_metadata

        workflow_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = []

        mock_draft = CatalogEntryDraft(id=10, snapshot_id=SNAPSHOT_ID_VALID, mapping_version="v1.0")
        workflow_service.draft_service.repository.save.side_effect = None
        workflow_service.draft_service.repository.save.return_value = mock_draft

        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_draft_phase(mock_db_session, run_id=TEST_RUN_UUID_1)

        assert result.draft is not None
        assert result.draft.id == 10

    def test_execute_draft_phase_mark_drafted_failure(self, workflow_service, mock_db_session):
        """Should mark failed when mark_drafted raises after draft creation."""
        mock_run = IngestionRun(
            run_id=TEST_RUN_UUID_1, snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version="v1.0", state=IngestionRunState.STORED,
        )
        workflow_service.ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        mock_metadata = [MagicMock(metadata_schema="name", value="Test")]
        workflow_service.metadata_entry_service.repository.select_metadata_entry.return_value = mock_metadata

        mock_relations = [MagicMock(catalog_column="title", metadata_column="name", correlation=0.95)]
        workflow_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = (
            mock_relations
        )

        mock_draft = CatalogEntryDraft(
            id=10, snapshot_id=SNAPSHOT_ID_VALID, mapping_version="v1.0", title="Test",
        )
        workflow_service.draft_service.repository.save.side_effect = None
        workflow_service.draft_service.repository.save.return_value = mock_draft

        def save_side_effect(*args, **kwargs):
            if workflow_service.ingestion_run_service.repository.save.call_count > 0:
                raise Exception("DB error on mark_drafted")
            return mock_run

        workflow_service.ingestion_run_service.repository.save.side_effect = save_side_effect

        with pytest.raises(Exception) as exc_info:
            workflow_service.execute_draft_phase(mock_db_session, run_id=TEST_RUN_UUID_1)

        assert "DB error" in str(exc_info.value)

    # ========================================================================
    # execute_merge_phase tests
    # ========================================================================

    def test_execute_merge_phase_no_candidates_low_score(
        self, workflow_service, mock_db_session, mock_catalog_merge_service, mock_catalog_entry_service
    ):
        """No external_ids → no candidates, PENDING, no auto-publish."""
        mock_draft = CatalogEntryDraft(id=10, snapshot_id=SNAPSHOT_ID_VALID, mapping_version="v1.0")
        workflow_service.draft_service.get_draft = MagicMock(return_value=mock_draft)

        mock_merge = CatalogMerge(id=1, draft_id=10)
        mock_catalog_merge_service.create_merge.return_value = mock_merge

        result = workflow_service.execute_merge_phase(mock_db_session, draft_id=10)

        assert result.merge == mock_merge
        assert result.auto_published is False
        mock_catalog_merge_service.approve_decision.assert_not_called()
        mock_catalog_entry_service.find_by_external_ids.assert_not_called()

    @patch("app.src.workflow.ingestion_workflow.IngestionWorkflowService.compute_mapping_score", return_value=0.95)
    def test_execute_merge_phase_with_candidates_above_threshold(
        self, _mock_score, workflow_service, mock_db_session, mock_catalog_merge_service, mock_catalog_entry_service
    ):
        """Candidates found + high score → auto-approve via execute_merge_approve."""
        mock_draft = CatalogEntryDraft(
            id=10, snapshot_id=SNAPSHOT_ID_VALID, mapping_version="v1.0",
            external_ids=["http://example.com/ds1"], title="Test",
        )
        workflow_service.draft_service.get_draft = MagicMock(return_value=mock_draft)

        mock_entry = CatalogEntry(id=42, external_ids=["http://example.com/ds1"])
        mock_catalog_entry_service.find_by_external_ids.return_value = [mock_entry]

        mock_merge = CatalogMerge(
            id=1, draft_id=10, mapping_score=0.95,
            merge_evidence={"recommended": {"entry_id": 42}, "decided": {"entry_id": 42}},
        )
        mock_catalog_merge_service.create_merge.return_value = mock_merge
        mock_catalog_merge_service.approve_decision.return_value = mock_merge

        mock_published_entry = CatalogEntry(id=99, identifier="entry-99")
        mock_catalog_entry_service.create_catalog_entry.return_value = mock_published_entry

        result = workflow_service.execute_merge_phase(mock_db_session, draft_id=10)

        assert result.auto_published is True
        assert result.catalog_entry_id == 99
        mock_catalog_merge_service.approve_decision.assert_called_once()
        mock_catalog_merge_service.create_merge.assert_called_once()

    @patch("app.src.workflow.ingestion_workflow.IngestionWorkflowService.compute_mapping_score", return_value=0.3)
    def test_execute_merge_phase_with_candidates_below_threshold(
        self, _mock_score, workflow_service, mock_db_session, mock_catalog_merge_service, mock_catalog_entry_service
    ):
        """Candidates found but low score → PENDING."""
        mock_draft = CatalogEntryDraft(
            id=10, snapshot_id=SNAPSHOT_ID_VALID, mapping_version="v1.0",
            external_ids=["http://example.com/ds1"],
        )
        workflow_service.draft_service.get_draft = MagicMock(return_value=mock_draft)

        mock_entry = CatalogEntry(id=42, external_ids=["http://example.com/ds1"])
        mock_catalog_entry_service.find_by_external_ids.return_value = [mock_entry]

        mock_merge = CatalogMerge(id=1, draft_id=10)
        mock_catalog_merge_service.create_merge.return_value = mock_merge

        result = workflow_service.execute_merge_phase(mock_db_session, draft_id=10)

        assert result.auto_published is False
        mock_catalog_merge_service.approve_decision.assert_not_called()

    def test_execute_merge_phase_draft_not_found(self, workflow_service, mock_db_session):
        """Draft not found → raises ValueError."""
        workflow_service.draft_service.get_draft = MagicMock(return_value=None)

        with pytest.raises(ValueError, match="Draft 999 not found"):
            workflow_service.execute_merge_phase(mock_db_session, draft_id=999)

    def test_execute_merge_phase_failure_publishes_event(
        self, workflow_service, mock_db_session, mock_event_bus, mock_catalog_entry_service
    ):
        """Merge failure → MergePhaseFailed event published."""
        mock_draft = CatalogEntryDraft(
            id=10, snapshot_id=SNAPSHOT_ID_VALID, mapping_version="v1.0",
            external_ids=["http://example.com/ds1"],
        )
        workflow_service.draft_service.get_draft = MagicMock(return_value=mock_draft)

        mock_catalog_entry_service.find_by_external_ids.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            workflow_service.execute_merge_phase(mock_db_session, draft_id=10)

        mock_event_bus.publish.assert_called()


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
        mock_event_bus,
    ):
        """Create IngestionWorkflowService with all mocked dependencies."""
        mock_catalog_entry_service = MagicMock(spec=CatalogEntryService)
        mock_catalog_merge_service = MagicMock(spec=CatalogMergeService)
        return IngestionWorkflowService(
            snapshot_service=MetadataSnapshotService(mock_metadata_snapshot_repository),
            metadata_entry_service=MetadataEntryService(mock_metadata_entry_repository),
            ingestion_run_service=IngestionRunService(mock_ingestion_run_repository),
            draft_service=CatalogEntryDraftService(
                mock_catalog_entry_draft_repository, mock_event_bus, mock_catalog_entry_service
            ),
            column_relation_service=ColumnRelationService(mock_column_relation_repository),
            file_storage=mock_file_storage,
            event_bus=mock_event_bus,
            catalog_merge_service=mock_catalog_merge_service,
            catalog_entry_service=mock_catalog_entry_service,
        )

    def test_store_phase_with_sample_json(self, workflow_service, mock_db_session, sample_schema_org_json):
        """Should process sample JSON file."""
        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_id = SNAPSHOT_ID_VALID
        workflow_service.snapshot_service.repository.save.side_effect = None
        workflow_service.snapshot_service.repository.save.return_value = mock_snapshot

        mock_run = MagicMock()
        mock_run.run_id = TEST_RUN_UUID_1
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
        mock_run.run_id = TEST_RUN_UUID_2
        workflow_service.ingestion_run_service.repository.save.side_effect = None
        workflow_service.ingestion_run_service.repository.save.return_value = mock_run

        result = workflow_service.execute_store_phase(mock_db_session, sample_dcat_rdf, filename="dcat.rdf")

        assert result.metadata_count > 0
