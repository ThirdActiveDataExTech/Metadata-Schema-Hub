from typing import List

from sqlalchemy import insert
from sqlmodel import select

from app.dependencies import SessionDep
from app.src.metadata_entry.model import MetadataEntry


class MetadataEntryRepository:
    """MetadataEntryRepository."""

    def save(self, db: SessionDep, metadata_entry: List[MetadataEntry]) -> List[MetadataEntry]:
        """Save metadata_entry."""
        values = [
            {
                "metadata_id": entry.metadata_id,
                "metadata_schema": entry.metadata_schema,
                "value": entry.value
            }
            for entry in metadata_entry
        ]

        # 특정 컬럼만 returning
        stmt = insert(MetadataEntry).values(values).returning(  # pyright: ignore
            MetadataEntry.id,
            MetadataEntry.metadata_id,
            MetadataEntry.metadata_schema,
            MetadataEntry.value,
            MetadataEntry.ingested_at
        )
        rows = db.exec(stmt).all()
        db.commit()

        # Row를 MetadataEntry로 변환
        return [
            MetadataEntry(
                id=row.id,
                metadata_id=row.metadata_id,
                metadata_schema=row.metadata_schema,
                value=row.value,
                ingested_at=row.ingested_at
            )
            for row in rows
        ]

    def select_metadata_entry(self, db: SessionDep, metadata_id: str) -> List[MetadataEntry]:
        """Select metadata_entry."""
        statement = select(MetadataEntry).where(MetadataEntry.metadata_id == metadata_id)
        results = db.exec(statement).all()
        return list(results)
