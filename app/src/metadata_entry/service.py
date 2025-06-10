from typing import List

from app.dependencies import SessionDep
from app.src.metadata_entry.json_converter import JsonConverter
from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.xml_converter import LxmlConverter


class MetadataEntryService:
    """MetadataEntryService."""

    def __init__(self, repository: MetadataEntryRepository):
        """Initialize Service."""
        self.repository = repository
        self.json_converter = JsonConverter()
        self.xml_converter = LxmlConverter()

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
