from typing import Any, Dict, List, Optional

from sqlalchemy import insert, or_
from sqlmodel import Session, select

from app.src.metadata_entry.model import MetadataEntry


class MetadataEntryRepository:
    """MetadataEntryRepository."""

    def save(self, db: Session, metadata_entries: List[MetadataEntry]) -> List[MetadataEntry]:
        """메타데이터 엔트리 저장."""
        values = [
            {"metadata_id": entry.metadata_id, "metadata_schema": entry.metadata_schema, "value": entry.value}
            for entry in metadata_entries
        ]

        # 특정 컬럼만 returning
        stmt = (
            insert(MetadataEntry)
            .values(values)
            .returning(  # pyright: ignore
                MetadataEntry.id,
                MetadataEntry.metadata_id,
                MetadataEntry.metadata_schema,
                MetadataEntry.value,
                MetadataEntry.ingested_at,
            )
        )

        rows = db.exec(stmt).all()

        return [
            MetadataEntry(
                id=row.id,
                metadata_id=row.metadata_id,
                metadata_schema=row.metadata_schema,
                value=row.value,
                ingested_at=row.ingested_at,
            )
            for row in rows
        ]

    def create_bulk(self, db: Session, creates: List[Dict[str, Any]]) -> None:
        """Bulk create using SQLAlchemy Core for performance"""
        db.bulk_insert_mappings(MetadataEntry, creates)

    def select_metadata_entry(self, db: Session, metadata_id: str) -> List[MetadataEntry]:
        """Select metadata_entry."""
        statement = select(MetadataEntry).where(MetadataEntry.metadata_id == metadata_id)
        results = db.exec(statement).all()
        return list(results)

    def select_metadata_entries_by_metadata_ids(self, db: Session, metadata_ids: List[str]) -> List[MetadataEntry]:
        """여러 identifier에 대한 metadata entries 일괄 조회."""
        stmt = select(MetadataEntry).where(MetadataEntry.metadata_id.in_(metadata_ids))  # pyright: ignore
        return list(db.exec(stmt).all())

    def search_metadata(
        self, db: Session, query: Optional[str] = None, schema: Optional[str] = None, metadata_id: Optional[str] = None
    ) -> List[MetadataEntry]:
        """검색 조건에 따른 메타데이터 엔트리 검색"""
        statement = select(MetadataEntry)

        conditions = []

        if query:
            # value 또는 metadata_schema에서 텍스트 검색
            conditions.append(
                or_(
                    MetadataEntry.value.ilike(f"%{query}%"),  # pyright: ignore
                    MetadataEntry.metadata_schema.ilike(f"%{query}%"),  # pyright: ignore
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

    def list_metadata_summary(self, db: Session, limit: Optional[int] = None) -> List[MetadataEntry]:
        """전체 메타데이터 목록 조회"""
        statement = select(MetadataEntry).order_by(MetadataEntry.ingested_at.desc())  # pyright: ignore

        if limit:
            statement = statement.limit(limit)

        results = db.exec(statement).all()
        return list(results)

    def select_distinct_metadata_schemas(self, db: Session, metadata_id_list: List[str]) -> List[str]:
        """주어진 메타데이터 id 로 스키마들을 조회."""
        statement = (
            select(MetadataEntry.metadata_schema)
            .where(MetadataEntry.metadata_id.in_(metadata_id_list))  # pyright: ignore
            .distinct()
        )

        results = db.exec(statement)
        return list(results)

    def get_all_distinct_metadata_schemas(self, db: Session) -> List[str]:
        """전체 DB에서 고유한 metadata_schema 목록 조회."""
        statement = select(MetadataEntry.metadata_schema).distinct()
        results = db.exec(statement)
        return list(results)
