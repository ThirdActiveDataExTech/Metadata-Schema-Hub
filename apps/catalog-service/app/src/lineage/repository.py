"""Repository for LineageEvent read operations."""

from uuid import UUID

from sqlmodel import Session, select

from app.src.lineage.model import LineageEvent

__all__ = ["LineageEventRepository"]


class LineageEventRepository:
    """Repository for lineage event read operations (catalog-service)."""

    def find_by_id(self, db: Session, event_id: int) -> LineageEvent | None:
        """Find event by ID."""
        return db.get(LineageEvent, event_id)

    def find_by_run_id(self, db: Session, run_id: UUID) -> list[LineageEvent]:
        """Find all events for a specific run."""
        stmt = (
            select(LineageEvent)
            .where(LineageEvent.run_id == run_id)
            .order_by(LineageEvent.event_time.asc())
        )
        return list(db.exec(stmt).all())

    def find_by_snapshot_id(
        self, db: Session, snapshot_id: str, limit: int = 100, offset: int = 0
    ) -> list[LineageEvent]:
        """Find events by snapshot_id."""
        stmt = (
            select(LineageEvent)
            .where(LineageEvent.snapshot_id == snapshot_id)
            .order_by(LineageEvent.event_time.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.exec(stmt).all())

    def find_by_catalog_entry_id(
        self, db: Session, catalog_entry_id: int
    ) -> list[LineageEvent]:
        """Find events by catalog_entry_id."""
        stmt = (
            select(LineageEvent)
            .where(LineageEvent.catalog_entry_id == catalog_entry_id)
            .order_by(LineageEvent.event_time.asc())
        )
        return list(db.exec(stmt).all())

    def find_all(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        job_name: str | None = None,
        event_type: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[LineageEvent]:
        """Find all events with optional filters."""
        stmt = select(LineageEvent)

        if job_name:
            stmt = stmt.where(LineageEvent.job_name == job_name)
        if event_type:
            stmt = stmt.where(LineageEvent.event_type == event_type)
        if snapshot_id:
            stmt = stmt.where(LineageEvent.snapshot_id == snapshot_id)

        stmt = stmt.order_by(LineageEvent.event_time.desc()).offset(offset).limit(limit)
        return list(db.exec(stmt).all())

    def count(
        self,
        db: Session,
        job_name: str | None = None,
        event_type: str | None = None,
        snapshot_id: str | None = None,
    ) -> int:
        """Count events with optional filters."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(LineageEvent)

        if job_name:
            stmt = stmt.where(LineageEvent.job_name == job_name)
        if event_type:
            stmt = stmt.where(LineageEvent.event_type == event_type)
        if snapshot_id:
            stmt = stmt.where(LineageEvent.snapshot_id == snapshot_id)

        result = db.exec(stmt).one()
        return result or 0
