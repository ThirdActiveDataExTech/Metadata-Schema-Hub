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

    def find_all(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        job_name: str | None = None,
        event_type: str | None = None,
    ) -> list[LineageEvent]:
        """Find all events with optional filters."""
        stmt = select(LineageEvent)

        if job_name:
            stmt = stmt.where(LineageEvent.job_name == job_name)
        if event_type:
            stmt = stmt.where(LineageEvent.event_type == event_type)

        stmt = stmt.order_by(LineageEvent.event_time.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
        return list(db.exec(stmt).all())

    def find_by_ref(self, db: Session, ref: str, limit: int = 100) -> list[LineageEvent]:
        """Find events where ref is in input_refs or output_refs.

        Uses GIN index on input_refs and output_refs arrays.
        """
        from sqlalchemy import or_

        stmt = (
            select(LineageEvent)
            .where(
                or_(
                    LineageEvent.input_refs.any(ref),  # type: ignore[attr-defined]
                    LineageEvent.output_refs.any(ref),  # type: ignore[attr-defined]
                )
            )
            .order_by(LineageEvent.event_time.desc())  # type: ignore[union-attr]
            .limit(limit)
        )
        return list(db.exec(stmt).all())
