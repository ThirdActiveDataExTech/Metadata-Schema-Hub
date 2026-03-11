"""Integration tests for IngestionRunRepository."""

from uuid import uuid4

import pytest
from sqlmodel import Session

from active_metadata.models import IngestionRunState
from app.src.ingestion_run.model import IngestionRun
from app.src.ingestion_run.repository import IngestionRunRepository
from app.src.metadata_snapshot.model import MetadataSnapshot
from tests.constants import NONEXISTENT_IDENTIFIER, NONEXISTENT_UUID, TEST_RUN_UUID_1


class TestSave:
    """Tests for save method."""

    def test_save_run(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
    ) -> None:
        """Should save ingestion run."""
        run = IngestionRun(
            run_id=TEST_RUN_UUID_1,
            snapshot_id="test-snapshot-id",
            state=IngestionRunState.STORED,
            mapping_version="v1.0",
        )

        result = ingestion_run_repository.save(db, run)

        assert result.run_id == TEST_RUN_UUID_1
        assert result.state == IngestionRunState.STORED


class TestFindByRunId:
    """Tests for find_by_run_id method."""

    def test_find_existing(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
        sample_ingestion_runs: list[IngestionRun],
    ) -> None:
        """Should return run when found."""
        run = sample_ingestion_runs[0]
        result = ingestion_run_repository.find_by_run_id(db, run.run_id)

        assert result is not None
        assert result.run_id == run.run_id

    def test_find_nonexistent(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
    ) -> None:
        """Should return None when not found."""
        result = ingestion_run_repository.find_by_run_id(db, NONEXISTENT_UUID)
        assert result is None


class TestFindBySnapshotId:
    """Tests for find_by_snapshot_id method."""

    def test_find_by_snapshot_id(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
        sample_ingestion_runs: list[IngestionRun],
        sample_metadata_snapshots: list[MetadataSnapshot],
    ) -> None:
        """Should return run for snapshot."""
        snapshot_id = str(sample_metadata_snapshots[0].snapshot_id)
        result = ingestion_run_repository.find_by_snapshot_id(db, snapshot_id)

        assert result is not None
        assert result.snapshot_id == snapshot_id

    def test_find_nonexistent(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
    ) -> None:
        """Should return None when not found."""
        result = ingestion_run_repository.find_by_snapshot_id(db, NONEXISTENT_IDENTIFIER)
        assert result is None


class TestFindByState:
    """Tests for find_by_state method."""

    def test_find_by_state(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
        sample_ingestion_runs: list[IngestionRun],
    ) -> None:
        """Should return runs with given state."""
        target_state = IngestionRunState.STORED
        result = ingestion_run_repository.find_by_state(db, target_state)
        expected_count = sum(1 for r in sample_ingestion_runs if r.state == target_state)
        assert len(result) == expected_count
        assert all(r.state == target_state for r in result)

    def test_find_drafted_state(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
        sample_ingestion_runs: list[IngestionRun],
    ) -> None:
        """Should return runs with DRAFTED state."""
        target_state = IngestionRunState.DRAFTED
        result = ingestion_run_repository.find_by_state(db, target_state)
        expected_count = sum(1 for r in sample_ingestion_runs if r.state == target_state)
        assert len(result) == expected_count
        assert result[0].draft_id is not None

    def test_find_no_matches(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
        sample_ingestion_runs: list[IngestionRun],
    ) -> None:
        """Should return empty list when no matches."""
        result = ingestion_run_repository.find_by_state(db, IngestionRunState.FAILED)
        assert result == []

    def test_find_with_limit(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
    ) -> None:
        """Should respect limit parameter."""
        # Create multiple runs with same state (UUID required)
        for i in range(5):
            run = IngestionRun(
                run_id=uuid4(),
                snapshot_id=f"test-snapshot-{i}",
                state=IngestionRunState.STORED,
                mapping_version="v1.0",
            )
            ingestion_run_repository.save(db, run)

        result = ingestion_run_repository.find_by_state(
            db, IngestionRunState.STORED, limit=3
        )
        assert len(result) == 3


class TestFindAll:
    """Tests for find_all method."""

    def test_find_all(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
        sample_ingestion_runs: list[IngestionRun],
    ) -> None:
        """Should return all runs."""
        result = ingestion_run_repository.find_all(db)
        assert len(result) == len(sample_ingestion_runs)

    def test_find_all_with_limit(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
        sample_ingestion_runs: list[IngestionRun],
    ) -> None:
        """Should respect limit parameter."""
        limit = 1
        result = ingestion_run_repository.find_all(db, limit=limit)
        assert len(result) == limit

    def test_find_all_empty(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
    ) -> None:
        """Should return empty list when no runs."""
        result = ingestion_run_repository.find_all(db)
        assert result == []

    def test_find_all_ordered_by_created_at_desc(
        self,
        db: Session,
        ingestion_run_repository: IngestionRunRepository,
        sample_ingestion_runs: list[IngestionRun],
    ) -> None:
        """Should return runs ordered by created_at descending."""
        result = ingestion_run_repository.find_all(db)

        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at
