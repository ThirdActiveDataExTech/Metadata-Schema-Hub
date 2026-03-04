import io
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd
from sqlmodel import Session

from app.src.catalog_entry.model import CatalogEntry, CatalogEntryCreate, CatalogEntrySummary, CatalogEntryUpdate
from app.src.catalog_entry.repository import CatalogEntryRepository


class CatalogEntryService:
    """CatalogEntryService."""

    def __init__(self, repository: CatalogEntryRepository):
        """Connect Repository."""
        self.repository = repository

    def create_catalog_entry(self, db: Session, catalog_entry: CatalogEntry) -> CatalogEntry:
        """CatalogEntry 생성."""
        return self.repository.save(db, catalog_entry)

    def create_catalog_entry_draft(self, db: Session, catalog_entry_create: CatalogEntryCreate) -> CatalogEntry:
        """CatalogEntry 초안 생성."""
        catalog_entry = CatalogEntry(
            identifier=catalog_entry_create.identifier,
            latest_snapshot_id=catalog_entry_create.latest_snapshot_id,
            ingested_at=catalog_entry_create.ingested_at,
        )
        catalog_entry = self.repository.save(db, catalog_entry)
        return catalog_entry

    def update_catalog_entry(
        self, db: Session, catalog_entry_id: int, catalog_entry_update: CatalogEntryUpdate
    ) -> CatalogEntry:
        """CatalogEntry 업데이트."""
        if not catalog_entry_update.has_changes():
            return self.repository.select(db, catalog_entry_id)

        catalog_entry = self.repository.select(db, catalog_entry_id)
        update_data = catalog_entry_update.model_dump_for_update()

        for field, value in update_data.items():
            setattr(catalog_entry, field, value)

        return self.repository.save(db, catalog_entry)

    def get_catalog_entry(self, db: Session, catalog_entry_id: int) -> CatalogEntry:
        """Get Catalog Entry."""
        return self.repository.select(db, catalog_entry_id)

    def get_catalog_entry_by_identifier(self, db: Session, catalog_entry_identifier: str) -> CatalogEntry:
        """Get Catalog Entry."""
        return self.repository.select_by_identifier(db, catalog_entry_identifier)

    def get_catalog_entries(self, db: Session, catalog_entry_ids: List[int]) -> List[CatalogEntry]:
        """Get Catalog Entries."""
        return self.repository.select_by_ids(db, catalog_entry_ids)

    def get_catalog_entries_by_identifier(self, db: Session, catalog_entry_identifiers: List[str]) -> List[CatalogEntry]:
        """Get Catalog Entry."""
        return self.repository.select_by_identifiers(db, catalog_entry_identifiers)

    def get_catalog_entry_summary_by_identifier(
        self, db: Session, catalog_entry_identifiers: List[str]
    ) -> List[CatalogEntrySummary]:
        """Get CatalogEntrySummary."""
        return self.repository.select_summaries_by_identifiers(db, catalog_entry_identifiers)

    def export_to_csv_stream(self, db: Session, limit: int = 100) -> io.StringIO:
        """메모리에서 CSV 스트림 생성"""
        data_list = self.repository.export_data_list(db, limit=limit)
        df = pd.DataFrame(data_list)

        # StringIO로 메모리에서 CSV 생성
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding="utf-8")
        csv_buffer.seek(0)

        return csv_buffer

    def list_catalog(self, db: Session, limit: Optional[int]) -> List[CatalogEntrySummary]:
        """전체 카탈로그 목록 조회"""
        return self.repository.list_catalog_summary(db, limit=limit)

    def search_catalog(
        self, db: Session, query: Optional[str] = None, keyword: Optional[str] = None
    ) -> Sequence[Dict[str, Any]]:
        """검색 조건에 따른 카탈로그 엔트리 검색."""
        items = self.repository.search_catalog(db=db, query=query, keyword=keyword)

        result_items = []
        for item in items:
            item_dict = item.model_dump()

            # 날짜 필드 문자열 변환
            if item_dict.get("issued"):
                item_dict["issued"] = str(item_dict["issued"])
            if item_dict.get("modified"):
                item_dict["modified"] = str(item_dict["modified"])
            if item_dict.get("ingested_at"):
                item_dict["ingested_at"] = str(item_dict["ingested_at"])
            if item_dict.get("updated_at"):
                item_dict["updated_at"] = str(item_dict["updated_at"])

            result_items.append(item_dict)

        return result_items

    def create_catalog_entry_bulk(self, db: Session, catalog_entries: List[Dict[str, Any]]) -> None:
        """CatalogEntry bulk 생성."""
        self.repository.create_bulk(db, catalog_entries)

    def update_catalog_entry_bulk(self, db: Session, catalog_entries: List[Dict[str, Any]]) -> None:
        """CatalogEntry bulk 업데이트."""
        self.repository.update_bulk(db, catalog_entries)
