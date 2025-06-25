import io
from typing import Any, Dict, List, Optional, Sequence, Literal

import pandas as pd
import xmltodict

from app.dependencies import SessionDep
from app.src.catalog_entry.model import CatalogEntry, CatalogEntrySummary, CatalogEntryCreate, CatalogEntryUpdate
from app.src.catalog_entry.repository import CatalogEntryRepository


class CatalogEntryService:
    """CatalogEntryService."""

    def __init__(self, repository: CatalogEntryRepository):
        """Connect Repository."""
        self.repository = repository

    def create_catalog_entry(self, db: SessionDep, catalog_entry_create: CatalogEntryCreate) -> CatalogEntry:
        """CatalogEntry 생성."""
        catalog_entry = CatalogEntry(
            identifier=catalog_entry_create.identifier,
            raw_metadata=catalog_entry_create.raw_metadata,
            ingested_at=catalog_entry_create.ingested_at,
        )
        catalog_entry = self.repository.save(db, catalog_entry)
        return catalog_entry

    def update_catalog_entry(
            self,
            db: SessionDep,
            catalog_entry_id: int,
            catalog_entry_update: CatalogEntryUpdate
    ) -> CatalogEntry:
        """CatalogEntry 업데이트."""
        if not catalog_entry_update.has_changes():
            return self.repository.select(db, catalog_entry_id)

        catalog_entry = self.repository.select(db, catalog_entry_id)
        update_data = catalog_entry_update.model_dump_for_update()

        for field, value in update_data.items():
            setattr(catalog_entry, field, value)

        return self.repository.save(db, catalog_entry)

    def get_catalog_entry(self, db: SessionDep, catalog_entry_id: int) -> CatalogEntry:
        """Get Catalog Entry."""
        return self.repository.select(db, catalog_entry_id)

    def get_catalog_entries(self, db: SessionDep, catalog_entry_ids: List[int]) -> List[CatalogEntry]:
        """Get Catalog Entries."""
        return self.repository.select_by_ids(db, catalog_entry_ids)

    def get_catalog_entries_by_identifier(
            self,
            db: SessionDep,
            catalog_entry_identifiers: List[str]
    ) -> List[CatalogEntry]:
        """Get Catalog Entry."""
        return self.repository.select_by_identifiers(db, catalog_entry_identifiers)

    def get_raw_metadata(
            self,
            db: SessionDep,
            catalog_entry_id: int,
            data_format: Literal["json", "xml"] = "json"
    ) -> Any:
        """Get raw metadata."""
        raw_metadata = self.repository.select(db, catalog_entry_id).raw_metadata

        if data_format == "xml":
            xml_string = xmltodict.unparse(raw_metadata, full_document=True)
            return xml_string

        return raw_metadata

    def get_raw_metadatas(self, db: SessionDep, catalog_entry_ids: List[int]) -> List[Any]:
        """Get raw metadatas for multiple catalog entries."""
        # WHERE IN 절로 단일 쿼리 실행
        entries = self.repository.select_by_ids(db, catalog_entry_ids)
        return [entry.raw_metadata for entry in entries]

    def export_to_csv_stream(self, db: SessionDep, limit: int = 100) -> io.StringIO:
        """메모리에서 CSV 스트림 생성"""
        data_list = self.repository.export_data_list(db, limit=limit)
        df = pd.DataFrame(data_list)

        # StringIO로 메모리에서 CSV 생성
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding="utf-8")
        csv_buffer.seek(0)

        return csv_buffer

    def list_catalog(self, db: SessionDep, limit: Optional[int]) -> List[CatalogEntrySummary]:
        """전체 카탈로그 목록 조회"""
        return self.repository.list_catalog_summary(db, limit=limit)

    def search_catalog(
            self,
            db: SessionDep,
            query: Optional[str] = None,
            keyword: Optional[str] = None
    ) -> Sequence[Dict[str, Any]]:
        """검색 조건에 따른 카탈로그 엔트리 검색."""
        items = self.repository.search_catalog(
            db=db,
            query=query,
            keyword=keyword
        )

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

            # raw_metadata 제거 (크기 최적화)
            item_dict.pop("raw_metadata", None)
            result_items.append(item_dict)

        return result_items

    def create_catalog_entry_bulk(self, db: SessionDep, catalog_entries: List[Dict[str, Any]]) -> None:
        """CatalogEntry bulk 생성."""
        self.repository.create_bulk(db, catalog_entries)

    def update_catalog_entry_bulk(self, db: SessionDep, catalog_entries: List[Dict[str, Any]]) -> None:
        """CatalogEntry bulk 업데이트."""
        self.repository.update_bulk(db, catalog_entries)
