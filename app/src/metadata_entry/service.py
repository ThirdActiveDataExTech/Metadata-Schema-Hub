from typing import List, Optional, Dict, Any

from app.dependencies import SessionDep
from app.src.metadata_entry.json_converter import JsonConverter
from app.src.metadata_entry.model import MetadataBase, MetadataEntry, MetadataCreate
from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.xml_converter import LxmlConverter


class MetadataEntryService:
    """MetadataEntryService."""

    def __init__(self, repository: MetadataEntryRepository):
        """Initialize Service."""
        self.repository = repository
        self.json_converter = JsonConverter()
        self.xml_converter = LxmlConverter()

    def create(self, db: SessionDep, metadata_create: MetadataCreate) -> List[MetadataEntry]:
        """Create MetadataEntry."""
        type_parser = {
            "json": self.json_converter.convert_to_table,
            "xml": self.xml_converter.convert_to_table,
        }
        parsed_data: List[MetadataBase] = type_parser[metadata_create.metadata_type](metadata_create.raw_metadata)
        entries = [
            MetadataEntry(metadata_id=metadata_create.metadata_id,
                          metadata_schema=item.metadata_schema, value=item.value)
            for item in parsed_data
        ]

        return self.repository.save(db, entries)

    def create_bulk(self, db: SessionDep, metadata_create_list: List[MetadataCreate]):
        """Create MetadataEntry in bulk."""
        type_parser = {
            "json": self.json_converter.convert_to_table,
            "xml": self.xml_converter.convert_to_table,
        }

        entries = [
            MetadataEntry(
                metadata_id=metadata_create.metadata_id,
                metadata_schema=item.metadata_schema,
                value=item.value,
            ).model_dump()
            for metadata_create in metadata_create_list
            for item in type_parser[metadata_create.metadata_type](metadata_create.raw_metadata)
        ]

        self.repository.create_bulk(db, entries)
        db.commit()

    def create_from_json(self, db: SessionDep, metadata_id: str, data: str | bytes) -> List[MetadataEntry]:
        """Create MetadataEntry from json."""
        parsed_data = self.json_converter.convert_to_table(data)

        entries = [
            MetadataEntry(
                metadata_id=metadata_id,
                metadata_schema=item.metadata_schema,
                value=item.value
            )
            for item in parsed_data
        ]

        return self.repository.save(db, entries)

    def create_from_xml(self, db: SessionDep, metadata_id: str, data: str | bytes) -> List[MetadataEntry]:
        """Create MetadataEntry from xml."""
        parsed_data = self.xml_converter.convert_to_table(data)

        entries = [
            MetadataEntry(
                metadata_id=metadata_id,
                metadata_schema=item.metadata_schema,
                value=item.value
            )
            for item in parsed_data
        ]

        return self.repository.save(db, entries)

    def select_metadata(self, db: SessionDep, metadata_id: str) -> List[MetadataEntry]:
        """Select MetadataEntry."""
        return self.repository.select_metadata_entry(db, metadata_id)

    def select_metadata_schemas_distinct(self, db: SessionDep, metadata_ids: List[str]) -> List[str]:
        """Select Metadata Schemas with DISTINCT."""
        return self.repository.select_distinct_metadata_schemas(db, metadata_ids)

    def select_metadata_bulk(self, db: SessionDep, metadata_ids: List[str]) -> List[MetadataEntry]:
        """여러 identifier에 대한 metadata entries 일괄 조회."""
        return self.repository.select_metadata_entries_by_metadata_ids(db, metadata_ids)

    def list_metadata(self, db: SessionDep, limit: Optional[int] = None) -> List[MetadataEntry]:
        """전체 메타데이터 목록 조회"""
        return self.repository.list_metadata_summary(db, limit=limit)

    def search_metadata(
            self,
            db: SessionDep,
            query: Optional[str] = None,
            schema: Optional[str] = None,
            metadata_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """검색 조건에 따른 메타데이터 엔트리 검색"""
        items = self.repository.search_metadata(
            db=db,
            query=query,
            schema=schema,
            metadata_id=metadata_id
        )

        result_items = []
        for item in items:
            item_dict = item.model_dump()

            # 날짜 필드 문자열 변환
            if item_dict.get("ingested_at"):
                item_dict["ingested_at"] = str(item_dict["ingested_at"])

            result_items.append(item_dict)

        return result_items
