import io
import uuid
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd
import xmltodict

from app.dependencies import SessionDep
from app.src.catalog_entry.exceptions import CatalogEntryNotFoundError
from app.src.catalog_entry.model import CatalogEntry, CatalogEntrySummary, CatalogEntryCreate
from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.column_relation.repository import ColumnRelationRepository
from app.src.metadata_entry.model import MetadataBase


class CatalogEntryService:
    """CatalogEntryService."""

    def __init__(self, repository: CatalogEntryRepository):
        """Connect Repository."""
        self.repository = repository

    def create_catalog_entry(self, db: SessionDep, catalog_entry_create: CatalogEntryCreate) -> CatalogEntry:
        """CatalogEntry 생성."""
        if not catalog_entry_create.identifier:
            catalog_entry_create.identifier = str(uuid.uuid1())
        catalog_entry = CatalogEntry(
            identifier=catalog_entry_create.identifier,
            raw_metadata=catalog_entry_create.raw_metadata,
            ingested_at=catalog_entry_create.ingested_at,
        )
        catalog_entry = self.repository.save(db, catalog_entry)
        return catalog_entry

    def get_raw_metadata(self, db: SessionDep, catalog_entry_id: int, data_format: str = "schema.org") -> Any:
        """Get raw metadata."""
        raw_metadata = self.repository.select(db, catalog_entry_id).raw_metadata

        if data_format == "dcat":
            xml_string = xmltodict.unparse(raw_metadata, full_document=True, pretty=True)
            return xml_string

        return raw_metadata

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


class CatalogEntryTransformService:
    """CatalogEntry 변환 service."""

    def __init__(
            self,
            catalog_entry_repository: CatalogEntryRepository,
            column_relation_repository: ColumnRelationRepository,
    ):
        """Connect Repository."""
        self.catalog_entry_repository = catalog_entry_repository
        self.column_relation_repository = column_relation_repository

    def update_catalog_entry_from_metadata_and_relation(
            self,
            db: SessionDep,
            catalog_entry_id: int,
            metadata_entries: List[MetadataBase],
    ) -> CatalogEntry:
        """CatalogEntry 를 메타데이터와 컬럼 관계 기반으로 매핑함."""
        catalog = self.catalog_entry_repository.select(db, catalog_entry_id)
        if not catalog:
            raise CatalogEntryNotFoundError(catalog_entry_id)

        metadata_dict = {item.metadata_schema: item.value for item in metadata_entries}
        metadata_columns = list(metadata_dict.keys())

        all_relations = self.column_relation_repository.select_relations_by_metadata_columns(db, metadata_columns)

        relations_by_catalog_column = {}
        for relation in all_relations:
            if relation.catalog_column not in relations_by_catalog_column:
                relations_by_catalog_column[relation.catalog_column] = []
            relations_by_catalog_column[relation.catalog_column].append(relation)

        for catalog_column in catalog.model_fields.keys():
            if getattr(catalog, catalog_column, None) is not None:  # 이미 catalog_entry 값이 있다면 건너뜀
                continue

            related_columns = relations_by_catalog_column.get(catalog_column, [])

            for related_column in related_columns:
                metadata_value = metadata_dict.get(related_column.metadata_column)
                if metadata_value:
                    setattr(catalog, catalog_column, metadata_value)
                    break

        return self.catalog_entry_repository.save(db, catalog)
