from typing import List, Optional

from sqlalchemy import or_
from sqlmodel import Session, select

from sqlmodel import Session
from app.src.metadata_entry.model import MetadataEntry


class MetadataEntryRepository:
    """MetadataEntryRepository."""

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
        if not metadata_id_list:
            return []

        statement = (
            select(MetadataEntry.metadata_schema)
            .where(MetadataEntry.metadata_id.in_(metadata_id_list))  # pyright: ignore
            .distinct()
        )

        # SQLModel의 exec().all()은 단일 컬럼 선택 시 스칼라 리스트 반환
        results = db.exec(statement).all()
        return list(results)
