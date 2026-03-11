"""Repository for LineageEvent read operations."""

from sqlalchemy import func, or_, text
from sqlmodel import Session, select

from app.src.lineage.model import LineageEvent

__all__ = ["LineageEventRepository"]


class LineageEventRepository:
    """Repository for lineage event read operations (catalog-service).

    Uses GIN index on input_refs and output_refs arrays.
    """

    def find_by_id(self, db: Session, event_id: int) -> LineageEvent | None:
        """Find event by ID."""
        return db.get(LineageEvent, event_id)

    def find_by_ref(
        self, db: Session, ref: str, limit: int = 100, offset: int = 0
    ) -> list[LineageEvent]:
        """Find events where ref is in input_refs or output_refs."""
        stmt = (
            select(LineageEvent)
            .where(
                or_(
                    LineageEvent.input_refs.any(ref),  # type: ignore[attr-defined]
                    LineageEvent.output_refs.any(ref),  # type: ignore[attr-defined]
                )
            )
            .order_by(LineageEvent.event_time.asc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        return list(db.exec(stmt).all())

    def find_by_input_ref(
        self, db: Session, ref: str, limit: int = 100
    ) -> list[LineageEvent]:
        """Find events where ref is in input_refs."""
        stmt = (
            select(LineageEvent)
            .where(LineageEvent.input_refs.any(ref))  # type: ignore[attr-defined]
            .order_by(LineageEvent.event_time.asc())  # type: ignore[union-attr]
            .limit(limit)
        )
        return list(db.exec(stmt).all())

    def find_by_output_ref(
        self, db: Session, ref: str, limit: int = 100
    ) -> list[LineageEvent]:
        """Find events where ref is in output_refs."""
        stmt = (
            select(LineageEvent)
            .where(LineageEvent.output_refs.any(ref))  # type: ignore[attr-defined]
            .order_by(LineageEvent.event_time.asc())  # type: ignore[union-attr]
            .limit(limit)
        )
        return list(db.exec(stmt).all())

    def find_downstream(self, db: Session, snapshot_ref: str, max_depth: int = 10) -> list[LineageEvent]:
        """Find all downstream events from a snapshot using recursive CTE.

        Traces: snapshot → draft → catalog_entry

        Note: Raw SQL is used instead of SQLAlchemy ORM because:
        1. Recursive CTE (WITH RECURSIVE) is verbose to express in SQLAlchemy
        2. PostgreSQL array overlap operator (&&) requires raw SQL
        3. Raw SQL provides better readability for this complex query
        """
        sql = text("""
            WITH RECURSIVE downstream AS (
                SELECT *, 0 as depth FROM lineage_event
                WHERE :ref = ANY(output_refs)

                UNION ALL

                SELECT e.*, d.depth + 1 FROM lineage_event e
                JOIN downstream d ON e.input_refs && d.output_refs
                WHERE d.depth < :max_depth
            )
            SELECT * FROM downstream ORDER BY depth, event_time
        """)
        result = db.execute(sql, {"ref": snapshot_ref, "max_depth": max_depth})
        return [
            LineageEvent(
                id=row.id,
                event_time=row.event_time,
                event_type=row.event_type,
                job_name=row.job_name,
                input_refs=row.input_refs,
                output_refs=row.output_refs,
                error_message=row.error_message,
                created_at=row.created_at,
            )
            for row in result.fetchall()
        ]

    def find_upstream(self, db: Session, catalog_ref: str, max_depth: int = 10) -> list[LineageEvent]:
        """Find all upstream events to a catalog entry using recursive CTE.

        Traces: catalog_entry → draft → snapshot → file (reverse)

        Note: Raw SQL is used instead of SQLAlchemy ORM because:
        1. Recursive CTE (WITH RECURSIVE) is verbose to express in SQLAlchemy
        2. PostgreSQL array overlap operator (&&) requires raw SQL
        3. Raw SQL provides better readability for this complex query
        """
        sql = text("""
            WITH RECURSIVE upstream AS (
                SELECT *, 0 as depth FROM lineage_event
                WHERE :ref = ANY(output_refs)

                UNION ALL

                SELECT e.*, u.depth + 1 FROM lineage_event e
                JOIN upstream u ON e.output_refs && u.input_refs
                WHERE u.depth < :max_depth
            )
            SELECT * FROM upstream ORDER BY depth DESC, event_time
        """)
        result = db.execute(sql, {"ref": catalog_ref, "max_depth": max_depth})
        return [
            LineageEvent(
                id=row.id,
                event_time=row.event_time,
                event_type=row.event_type,
                job_name=row.job_name,
                input_refs=row.input_refs,
                output_refs=row.output_refs,
                error_message=row.error_message,
                created_at=row.created_at,
            )
            for row in result.fetchall()
        ]

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

    def count(
        self,
        db: Session,
        job_name: str | None = None,
        event_type: str | None = None,
    ) -> int:
        """Count events with optional filters."""
        stmt = select(func.count()).select_from(LineageEvent)

        if job_name:
            stmt = stmt.where(LineageEvent.job_name == job_name)
        if event_type:
            stmt = stmt.where(LineageEvent.event_type == event_type)

        result = db.exec(stmt).one()
        return result or 0
