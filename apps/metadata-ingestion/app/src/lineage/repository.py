"""Repository for LineageEvent persistence."""

from sqlmodel import Session, select

from app.src.lineage.model import LineageEvent

__all__ = ["LineageEventRepository"]


class LineageEventRepository:
    """Repository for lineage event CRUD operations."""

    def save(self, db: Session, event: LineageEvent) -> LineageEvent:
        """Save a lineage event to database."""
        db.add(event)
        db.flush()
        db.refresh(event)
        return event

    def find_by_id(self, db: Session, event_id: int) -> LineageEvent | None:
        """Find event by ID."""
        return db.get(LineageEvent, event_id)

    def find_by_snapshot_id(
        self, db: Session, snapshot_id: str, limit: int = 100, offset: int = 0
    ) -> list[LineageEvent]:
        """Find events by snapshot_id."""
        stmt = (
            select(LineageEvent)
            .where(LineageEvent.snapshot_id == snapshot_id)
            .order_by(LineageEvent.event_time.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.exec(stmt).all())

    def find_by_job_name(
        self, db: Session, job_name: str, limit: int = 100, offset: int = 0
    ) -> list[LineageEvent]:
        """Find events by job name."""
        stmt = (
            select(LineageEvent)
            .where(LineageEvent.job_name == job_name)
            .order_by(LineageEvent.event_time.desc())
            .offset(offset)
            .limit(limit)
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
