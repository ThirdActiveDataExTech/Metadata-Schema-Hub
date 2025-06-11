from typing import List, Optional

from sqlalchemy import insert, or_
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

    def search_metadata(
            self,
            db: SessionDep,
            query: Optional[str] = None,
            schema: Optional[str] = None,
            metadata_id: Optional[str] = None
    ) -> List[MetadataEntry]:
        """검색 조건에 따른 메타데이터 엔트리 검색"""
        statement = select(MetadataEntry)

        conditions = []

        if query:
            # value 또는 metadata_schema에서 텍스트 검색
            conditions.append(
                or_(
                    MetadataEntry.value.ilike(f"%{query}%"),  # pyright: ignore
                    MetadataEntry.metadata_schema.ilike(f"%{query}%")  # pyright: ignore
                )
            )

        if schema:
            # metadata_schema 정확 일치
            conditions.append(MetadataEntry.metadata_schema == schema)

        if metadata_id:
            # metadata_id 정확 일치
            conditions.append(MetadataEntry.metadata_id == metadata_id)

        if conditions:
            statement = statement.where(*conditions)

        results = db.exec(statement).all()
        return list(results)

    def list_metadata_summary(self, db: SessionDep, limit: Optional[int] = None) -> List[MetadataEntry]:
        """전체 메타데이터 목록 조회"""
        statement = select(MetadataEntry).order_by(MetadataEntry.ingested_at.desc())  # pyright: ignore

        if limit:
            statement = statement.limit(limit)

        results = db.exec(statement).all()
        return list(results)
