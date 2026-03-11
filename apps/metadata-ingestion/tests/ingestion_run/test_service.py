"""Tests for IngestionRunService."""

from unittest.mock import MagicMock

import pytest

from active_metadata.models import IngestionRunState
from tests.constants import (
    NONEXISTENT_UUID,
    SNAPSHOT_ID_VALID,
    TEST_MAPPING_VERSION,
    TEST_RUN_UUID_1,
    TEST_RUN_UUID_2,
)
from app.src.ingestion_run.model import IngestionRun, IngestionRunCreate
from app.src.ingestion_run.service import IngestionRunService


class TestIngestionRunService:
    """Test cases for IngestionRunService."""

    # ========================================================================
    # create_run tests
    # ========================================================================

    def test_create_run_sets_stored_state(self, ingestion_run_service, mock_db_session):
        """Should create run with STORED state."""
        request = IngestionRunCreate(
            run_id=TEST_RUN_UUID_1,
            snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version=TEST_MAPPING_VERSION,
        )

        ingestion_run_service.repository.save.side_effect = lambda db, r: r

        result = ingestion_run_service.create_run(mock_db_session, request)

        assert isinstance(result, IngestionRun)
        assert result.run_id == TEST_RUN_UUID_1
        assert result.snapshot_id == SNAPSHOT_ID_VALID
        assert result.mapping_version == TEST_MAPPING_VERSION
        assert result.state == IngestionRunState.STORED

    def test_create_run_calls_repository(self, ingestion_run_service, mock_db_session):
        """Should call repository.save."""
        request = IngestionRunCreate(
            run_id=TEST_RUN_UUID_2,
            snapshot_id=SNAPSHOT_ID_VALID,
            mapping_version=TEST_MAPPING_VERSION,
        )

        ingestion_run_service.create_run(mock_db_session, request)

        ingestion_run_service.repository.save.assert_called_once()

    # ========================================================================
    # mark_drafted tests
    # ========================================================================

    def test_mark_drafted_success(self, ingestion_run_service, mock_db_session):
        """Should transition from STORED to DRAFTED."""
        mock_run = MagicMock(spec=IngestionRun)
        mock_run.state = IngestionRunState.STORED
        ingestion_run_service.repository.find_by_run_id.return_value = mock_run
        ingestion_run_service.repository.save.side_effect = lambda db, r: r

        result = ingestion_run_service.mark_drafted(mock_db_session, run_id=TEST_RUN_UUID_1, draft_id=10)

        assert result.state == IngestionRunState.DRAFTED
        assert result.draft_id == 10

    def test_mark_drafted_run_not_found(self, ingestion_run_service, mock_db_session):
        """Should raise ValueError when run not found."""
        ingestion_run_service.repository.find_by_run_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            ingestion_run_service.mark_drafted(mock_db_session, run_id=NONEXISTENT_UUID, draft_id=10)

        assert "not found" in str(exc_info.value)

    def test_mark_drafted_wrong_state(self, ingestion_run_service, mock_db_session):
        """Should raise ValueError when not in STORED state."""
        mock_run = MagicMock(spec=IngestionRun)
        mock_run.state = IngestionRunState.DRAFTED  # Already drafted
        ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        with pytest.raises(ValueError) as exc_info:
            ingestion_run_service.mark_drafted(mock_db_session, run_id=TEST_RUN_UUID_1, draft_id=10)

        assert "DRAFTED" in str(exc_info.value)

    def test_mark_drafted_from_failed_state(self, ingestion_run_service, mock_db_session):
        """Should raise ValueError when attempting FAILED -> DRAFTED transition."""
        mock_run = MagicMock(spec=IngestionRun)
        mock_run.state = IngestionRunState.FAILED
        ingestion_run_service.repository.find_by_run_id.return_value = mock_run

        with pytest.raises(ValueError) as exc_info:
            ingestion_run_service.mark_drafted(mock_db_session, run_id=TEST_RUN_UUID_1, draft_id=10)

        assert "FAILED" in str(exc_info.value)

    # ========================================================================
    # mark_failed tests
    # ========================================================================

    def test_mark_failed_success(self, ingestion_run_service, mock_db_session):
        """Should set FAILED state and error message."""
        mock_run = MagicMock(spec=IngestionRun)
        mock_run.state = IngestionRunState.STORED
        ingestion_run_service.repository.find_by_run_id.return_value = mock_run
        ingestion_run_service.repository.save.side_effect = lambda db, r: r

        result = ingestion_run_service.mark_failed(mock_db_session, run_id=TEST_RUN_UUID_1, error="Parse error")

        assert result.state == IngestionRunState.FAILED
        assert result.error == "Parse error"

    def test_mark_failed_run_not_found(self, ingestion_run_service, mock_db_session):
        """Should raise ValueError when run not found."""
        ingestion_run_service.repository.find_by_run_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            ingestion_run_service.mark_failed(mock_db_session, run_id=NONEXISTENT_UUID, error="error")

        assert "not found" in str(exc_info.value)

    def test_mark_failed_from_drafted_state(self, ingestion_run_service, mock_db_session):
        """Should allow DRAFTED -> FAILED transition (no state restriction)."""
        mock_run = MagicMock(spec=IngestionRun)
        mock_run.state = IngestionRunState.DRAFTED
        ingestion_run_service.repository.find_by_run_id.return_value = mock_run
        ingestion_run_service.repository.save.side_effect = lambda db, r: r

        result = ingestion_run_service.mark_failed(mock_db_session, run_id=TEST_RUN_UUID_1, error="Late failure")

        assert result.state == IngestionRunState.FAILED
        assert result.error == "Late failure"

    def test_mark_failed_from_failed_state(self, ingestion_run_service, mock_db_session):
        """Should allow updating error on already FAILED run."""
        mock_run = MagicMock(spec=IngestionRun)
        mock_run.state = IngestionRunState.FAILED
        mock_run.error = "Original error"
        ingestion_run_service.repository.find_by_run_id.return_value = mock_run
        ingestion_run_service.repository.save.side_effect = lambda db, r: r

        result = ingestion_run_service.mark_failed(mock_db_session, run_id=TEST_RUN_UUID_1, error="Updated error")

        assert result.state == IngestionRunState.FAILED
        assert result.error == "Updated error"

    # ========================================================================
    # get_pending_runs tests
    # ========================================================================

    def test_get_pending_runs(self, ingestion_run_service, mock_db_session):
        """Should return runs in STORED state."""
        expected = [MagicMock(), MagicMock()]
        ingestion_run_service.repository.find_by_state.return_value = expected

        result = ingestion_run_service.get_pending_runs(mock_db_session, limit=50)

        assert result == expected
        ingestion_run_service.repository.find_by_state.assert_called_once_with(
            mock_db_session, IngestionRunState.STORED, 50
        )

    def test_get_pending_runs_default_limit(self, ingestion_run_service, mock_db_session):
        """Should use default limit of 100."""
        ingestion_run_service.repository.find_by_state.return_value = []

        ingestion_run_service.get_pending_runs(mock_db_session)

        ingestion_run_service.repository.find_by_state.assert_called_once_with(
            mock_db_session, IngestionRunState.STORED, 100
        )

    # ========================================================================
    # get_runs_by_state tests
    # ========================================================================

    def test_get_runs_by_state(self, ingestion_run_service, mock_db_session):
        """Should return runs filtered by state."""
        expected = [MagicMock()]
        ingestion_run_service.repository.find_by_state.return_value = expected

        result = ingestion_run_service.get_runs_by_state(mock_db_session, IngestionRunState.DRAFTED, limit=10)

        assert result == expected
        ingestion_run_service.repository.find_by_state.assert_called_once_with(
            mock_db_session, IngestionRunState.DRAFTED, 10
        )

    # ========================================================================
    # get_run_by_snapshot_id tests
    # ========================================================================

    def test_get_run_by_snapshot_id_found(self, ingestion_run_service, mock_db_session):
        """Should return run for snapshot_id."""
        expected = MagicMock(spec=IngestionRun)
        ingestion_run_service.repository.find_by_snapshot_id.return_value = expected

        result = ingestion_run_service.get_run_by_snapshot_id(mock_db_session, "snap-123")

        assert result == expected
        ingestion_run_service.repository.find_by_snapshot_id.assert_called_once_with(mock_db_session, "snap-123")

    def test_get_run_by_snapshot_id_not_found(self, ingestion_run_service, mock_db_session):
        """Should return None when not found."""
        ingestion_run_service.repository.find_by_snapshot_id.return_value = None

        result = ingestion_run_service.get_run_by_snapshot_id(mock_db_session, "nonexistent")

        assert result is None

    # ========================================================================
    # get_run tests
    # ========================================================================

    def test_get_run_found(self, ingestion_run_service, mock_db_session):
        """Should return run by ID."""
        expected = MagicMock(spec=IngestionRun)
        ingestion_run_service.repository.find_by_run_id.return_value = expected

        result = ingestion_run_service.get_run(mock_db_session, TEST_RUN_UUID_1)

        assert result == expected
        ingestion_run_service.repository.find_by_run_id.assert_called_once_with(mock_db_session, TEST_RUN_UUID_1)

    def test_get_run_not_found(self, ingestion_run_service, mock_db_session):
        """Should return None when not found."""
        ingestion_run_service.repository.find_by_run_id.return_value = None

        result = ingestion_run_service.get_run(mock_db_session, NONEXISTENT_UUID)

        assert result is None

    # ========================================================================
    # get_all_runs tests
    # ========================================================================

    def test_get_all_runs(self, ingestion_run_service, mock_db_session):
        """Should return all runs with limit."""
        expected = [MagicMock(), MagicMock(), MagicMock()]
        ingestion_run_service.repository.find_all.return_value = expected

        result = ingestion_run_service.get_all_runs(mock_db_session, limit=50)

        assert result == expected
        ingestion_run_service.repository.find_all.assert_called_once_with(mock_db_session, 50)

    def test_get_all_runs_default_limit(self, ingestion_run_service, mock_db_session):
        """Should use default limit of 100."""
        ingestion_run_service.repository.find_all.return_value = []

        ingestion_run_service.get_all_runs(mock_db_session)

        ingestion_run_service.repository.find_all.assert_called_once_with(mock_db_session, 100)
