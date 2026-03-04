import json
from typing import List, Optional, Sequence, Dict, Any

from sqlalchemy import and_, or_
from sqlmodel import Session, select

from app.src.catalog_entry.exceptions import CatalogEntryNotFoundError
from app.src.catalog_entry.model import CatalogEntry, CatalogEntrySummary


class CatalogEntryRepository:
    """CatalogEntryRepository."""

    def save(self, db: Session, catalog_entry: CatalogEntry) -> CatalogEntry:
        """Save catalog_entry."""
        db.add(catalog_entry)
        return catalog_entry

    def select(self, db: Session, catalog_entry_id: int) -> CatalogEntry:
        """Select catalog_entry."""
        catalog_entry = db.get(CatalogEntry, catalog_entry_id)
        if not catalog_entry:
            raise CatalogEntryNotFoundError.by_id(catalog_entry_id)

        return catalog_entry

    def select_by_identifier(self, db: Session, catalog_entry_identifier: str) -> CatalogEntry:
        """Select catalog_entry by identifier."""
        stmt = select(CatalogEntry).where(CatalogEntry.identifier == catalog_entry_identifier)
        catalog_entry = db.exec(stmt).first()
        if not catalog_entry:
            raise CatalogEntryNotFoundError.by_identifier(catalog_entry_identifier)
        return catalog_entry

    def select_by_ids(self, db: Session, catalog_entry_ids: List[int]) -> List[CatalogEntry]:
        """Select multiple catalog entries by ids."""
        stmt = select(CatalogEntry).where(CatalogEntry.id.in_(catalog_entry_ids))  # pyright: ignore
        return list(db.exec(stmt).all())

    def select_by_identifiers(self, db: Session, catalog_entry_identifiers: List[str]) -> List[CatalogEntry]:
        """Select catalog entries by identifiers."""
        stmt = select(CatalogEntry).where(CatalogEntry.identifier.in_(catalog_entry_identifiers))  # pyright: ignore
        return list(db.exec(stmt).all())

    def select_summaries_by_identifiers(
        self, db: Session, catalog_entry_identifiers: List[str]
    ) -> List[CatalogEntrySummary]:
        """Select catalog entry summaries by identifiers."""
        statement = select(  # pyright: ignore
            CatalogEntry.id,
            CatalogEntry.title,
            CatalogEntry.issued,
            CatalogEntry.modified,
            CatalogEntry.identifier,
            CatalogEntry.publisher,
            CatalogEntry.keyword,
            CatalogEntry.landing_page,
            CatalogEntry.theme,
            CatalogEntry.access_url,
            CatalogEntry.ingested_at,
            CatalogEntry.updated_at,
        ).where(CatalogEntry.identifier.in_(catalog_entry_identifiers))  # pyright: ignore

        rows = db.exec(statement).all()

        return [
            CatalogEntrySummary(
                id=row.id,
                title=row.title,
                issued=str(row.issued) if row.issued else None,
                modified=str(row.modified) if row.modified else None,
                identifier=row.identifier,
                publisher=row.publisher,
                keyword=row.keyword,
                landing_page=row.landing_page,
                theme=row.theme,
                access_url=row.access_url,
                ingested_at=str(row.ingested_at) if row.ingested_at else None,
                updated_at=str(row.updated_at) if row.updated_at else None,
            )
            for row in rows
        ]

    def export_data_list(self, db: Session, limit: int = None):
        """데이터베이스의 catalog_entry 테이블 전체를 list로 내보냄."""
        # 모든 레코드 조회 쿼리 작성 (필요시 limit 추가)
        statement = select(CatalogEntry)
        if limit:
            statement = statement.limit(limit)

        # 쿼리 실행
        results = db.exec(statement).all()

        if not results:
            print("내보낼 데이터가 없습니다.")
            return None

        # 결과를 딕셔너리 리스트로 변환
        data_list = []
        for result in results:
            # SQLModel 0.0.14부터 dict() 대신 model_dump() 사용
            data = result.model_dump()

            # 날짜 필드 문자열 변환
            if "issued" in data and data["issued"]:
                data["issued"] = str(data["issued"])

            if "modified" in data and data["modified"]:
                data["modified"] = str(data["modified"])

            if "ingested_at" in data and data["ingested_at"]:
                data["ingested_at"] = str(data["ingested_at"])

            if "updated_at" in data and data["updated_at"]:
                data["updated_at"] = str(data["updated_at"])

            # JSONB 필드는 문자열로 변환하여 CSV에 저장
            if "publisher" in data and isinstance(data["publisher"], dict):
                data["publisher"] = json.dumps(data["publisher"], ensure_ascii=False)

            # 배열 타입 필드 (keyword, theme)도 문자열로 변환
            if "keyword" in data and isinstance(data["keyword"], list):
                data["keyword"] = ",".join(data["keyword"]) if data["keyword"] else ""

            if "theme" in data and isinstance(data["theme"], list):
                data["theme"] = ",".join(data["theme"]) if data["theme"] else ""

            data_list.append(data)

        return data_list

    def list_catalog_summary(self, db: Session, limit: Optional[int] = None) -> List[CatalogEntrySummary]:
        """요약된 카탈로그 목록 조회."""
        statement = select(  # type: ignore
            CatalogEntry.id,
            CatalogEntry.title,
            CatalogEntry.issued,
            CatalogEntry.modified,
            CatalogEntry.identifier,
            CatalogEntry.publisher,
            CatalogEntry.keyword,
            CatalogEntry.landing_page,
            CatalogEntry.theme,
            CatalogEntry.access_url,
            CatalogEntry.ingested_at,
            CatalogEntry.updated_at,
        )

        if limit is not None:
            statement = statement.limit(limit)

        rows = db.exec(statement).all()

        return [
            CatalogEntrySummary(
                id=row.id,
                title=row.title,
                issued=str(row.issued) if row.issued else None,
                modified=str(row.modified) if row.modified else None,
                identifier=row.identifier,
                publisher=row.publisher,
                keyword=row.keyword,
                landing_page=row.landing_page,
                theme=row.theme,
                access_url=row.access_url,
                ingested_at=str(row.ingested_at) if row.ingested_at else None,
                updated_at=str(row.updated_at) if row.updated_at else None,
            )
            for row in rows
        ]

    def search_catalog(
        self, db: Session, query: Optional[str] = None, keyword: Optional[str] = None
    ) -> Sequence[CatalogEntry]:
        """검색 조건에 따른 카탈로그 엔트리 검색"""
        statement = select(CatalogEntry)
        conditions = []

        # 텍스트 검색 (제목, 설명에서 ILIKE 검색)
        if query:
            text_condition = or_(
                CatalogEntry.title.ilike(f"%{query}%"),  # type: ignore
                CatalogEntry.description.ilike(f"%{query}%"),  # type: ignore
            )
            conditions.append(text_condition)

        # 키워드 필터 (PostgreSQL 배열 컬럼에서 ANY 검색)
        if keyword:
            keyword_condition = CatalogEntry.keyword.any(keyword)  # type: ignore
            conditions.append(keyword_condition)

        # 조건 적용
        if conditions:
            where_condition = and_(*conditions)
            statement = statement.where(where_condition)

        # 결과 조회
        results = db.exec(statement).all()

        return results

    def create_bulk(self, db: Session, creates: List[Dict[str, Any]]) -> None:
        """Bulk create using SQLAlchemy Core for performance"""
        if not creates:
            return

        db.bulk_insert_mappings(CatalogEntry, creates)

    def update_bulk(self, db: Session, updates: List[Dict[str, Any]]) -> None:
        """Bulk update using SQLAlchemy Core for performance"""
        if not updates:
            return

        db.bulk_update_mappings(CatalogEntry, updates)
