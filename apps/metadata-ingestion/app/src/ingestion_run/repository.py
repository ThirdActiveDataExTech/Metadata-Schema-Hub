"""Database operations for IngestionRun."""

from typing import Optional
from uuid import UUID

from active_metadata.models import IngestionRunState
from sqlmodel import Session, select

from app.src.ingestion_run.model import IngestionRun


class IngestionRunRepository:
    """IngestionRun repository."""

    def save(self, db: Session, run: IngestionRun) -> IngestionRun:
        """Save ingestion run to database."""
        db.add(run)
        db.flush()
        return run

    def find_by_run_id(self, db: Session, run_id: UUID) -> Optional[IngestionRun]:
        """Find run by run_id."""
        stmt = select(IngestionRun).where(IngestionRun.run_id == run_id)
        return db.exec(stmt).first()

    def find_by_snapshot_id(self, db: Session, snapshot_id: str) -> Optional[IngestionRun]:
        """Find run by snapshot_id (1:1 relationship)."""
        stmt = select(IngestionRun).where(IngestionRun.snapshot_id == snapshot_id)
        return db.exec(stmt).first()

    def find_by_state(self, db: Session, state: IngestionRunState, limit: int = 100) -> list[IngestionRun]:
        """Find runs by state."""
        stmt = (
            select(IngestionRun)
            .where(IngestionRun.state == state)
            .order_by(IngestionRun.created_at.desc())  # type: ignore[union-attr]
            .limit(limit)
        )
        return list(db.exec(stmt).all())

    def find_all(self, db: Session, limit: int = 100) -> list[IngestionRun]:
        """Find all runs."""
        stmt = (
            select(IngestionRun)
            .order_by(IngestionRun.created_at.desc())  # type: ignore[union-attr]
            .limit(limit)
        )
        return list(db.exec(stmt).all())
