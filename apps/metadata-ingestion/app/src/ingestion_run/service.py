"""Business logic for IngestionRun."""

from typing import Optional
from uuid import UUID

from active_metadata.models import IngestionRunState
from sqlmodel import Session

from app.src.ingestion_run.model import IngestionRun, IngestionRunCreate
from app.src.ingestion_run.repository import IngestionRunRepository


class IngestionRunService:
    """IngestionRun service."""

    def __init__(self, repository: IngestionRunRepository):
        """Initialize with repository."""
        self.repository = repository

    def create_run(self, db: Session, request: IngestionRunCreate) -> IngestionRun:
        """Create new ingestion run (TX1 - STORED state).

        run_id is UUID, shared with lineage_run_event for direct JOIN.
        """
        run = IngestionRun(
            run_id=request.run_id,  # App-generated UUID
            snapshot_id=request.snapshot_id,
            mapping_version=request.mapping_version,
            state=IngestionRunState.STORED,
        )
        return self.repository.save(db, run)

    def mark_drafted(self, db: Session, run_id: UUID, draft_id: int) -> Optional[IngestionRun]:
        """Mark run as DRAFTED after TX2 completion."""
        run = self.repository.find_by_run_id(db, run_id)
        if not run:
            raise ValueError(f"IngestionRun with id {run_id} not found")

        if run.state != IngestionRunState.STORED:
            raise ValueError(f"Cannot mark run as DRAFTED. Current state: {run.state}")

        run.state = IngestionRunState.DRAFTED
        run.draft_id = draft_id
        return self.repository.save(db, run)

    def mark_failed(self, db: Session, run_id: UUID, error: str) -> Optional[IngestionRun]:
        """Mark run as FAILED with error message."""
        run = self.repository.find_by_run_id(db, run_id)
        if not run:
            raise ValueError(f"IngestionRun with id {run_id} not found")

        run.state = IngestionRunState.FAILED
        run.error = error
        return self.repository.save(db, run)

    def get_pending_runs(self, db: Session, limit: int = 100) -> list[IngestionRun]:
        """Get runs awaiting TX2 processing (STORED state)."""
        return self.repository.find_by_state(db, IngestionRunState.STORED, limit)

    def get_runs_by_state(self, db: Session, state: IngestionRunState, limit: int = 100) -> list[IngestionRun]:
        """Get runs by state."""
        return self.repository.find_by_state(db, state, limit)

    def get_run_by_snapshot_id(self, db: Session, snapshot_id: str) -> Optional[IngestionRun]:
        """Get run by SnapshotID."""
        return self.repository.find_by_snapshot_id(db, snapshot_id)

    def get_run(self, db: Session, run_id: UUID) -> Optional[IngestionRun]:
        """Get run by ID (UUID)."""
        return self.repository.find_by_run_id(db, run_id)

    def get_all_runs(self, db: Session, limit: int = 100) -> list[IngestionRun]:
        """Get all runs."""
        return self.repository.find_all(db, limit)
