import logging
from typing import Any, Dict, List

from app.dependencies import SessionDep
from app.src.catalog_entry.model import CatalogEntry, CatalogEntryUpdate
from app.src.catalog_entry.service import CatalogEntryService
from app.src.column_relation.model import ColumnRelation
from app.src.column_relation.service import ColumnRelationService
from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_entry.service import MetadataEntryService


class CatalogEntryTransformService:
    """CatalogEntry 변환 service."""

    def __init__(
        self,
        catalog_entry_service: CatalogEntryService,
        column_relation_service: ColumnRelationService,
        metadata_entry_service: MetadataEntryService,
    ):
        """DI Services."""
        self.catalog_entry_service = catalog_entry_service
        self.column_relation_service = column_relation_service
        self.metadata_entry_service = metadata_entry_service

    def _apply_metadata_to_update(
        self,
        catalog_entry_update: CatalogEntryUpdate,
        metadata_entries: List[MetadataEntry],
        relations: List[ColumnRelation],
    ) -> None:
        """메타데이터를 catalog entry update에 직접 적용."""
        # Dict 변환 (O(1) 조회를 위해)
        metadata_dict: Dict[str, Any] = {entry.metadata_schema: entry.value for entry in metadata_entries}

        processed_columns = set()

        # Sort by correlation (highest first)
        sorted_relations = sorted(relations, key=lambda r: r.correlation if r.correlation else 0, reverse=True)

        for relation in sorted_relations:
            # Skip already processed columns (maintain highest correlation)
            if relation.catalog_column in processed_columns:
                continue

            # Skip invalid fields
            if relation.catalog_column not in CatalogEntryUpdate.model_fields:
                continue

            metadata_value = metadata_dict.get(relation.metadata_column)
            if metadata_value is not None:
                catalog_entry_update.set_field(relation.catalog_column, metadata_value)
                processed_columns.add(relation.catalog_column)

    def transform_catalog_entry(
        self,
        db: SessionDep,
        catalog_entry_id: int,
    ) -> CatalogEntry:
        """CatalogEntry를 메타데이터와 컬럼 관계 기반으로 변환."""
        catalog_entry = self.catalog_entry_service.get_catalog_entry(db, catalog_entry_id)
        metadata_entries = self.metadata_entry_service.select_metadata(db, catalog_entry.identifier)

        if not metadata_entries:
            logging.warning(f"No metadata found for catalog_entry_id={catalog_entry_id}")
            return catalog_entry

        # Get relations for all metadata schemas
        metadata_schemas = [entry.metadata_schema for entry in metadata_entries]
        all_relations = self.column_relation_service.get_relations_by_metadata_columns(db, metadata_schemas)

        # Apply transformation
        catalog_entry_update = CatalogEntryUpdate()
        self._apply_metadata_to_update(catalog_entry_update, metadata_entries, all_relations)

        # Update if any fields were set
        if any(getattr(catalog_entry_update, field) is not None for field in CatalogEntryUpdate.model_fields):
            return self.catalog_entry_service.update_catalog_entry(db, catalog_entry.id, catalog_entry_update)

        return catalog_entry

    def transform_catalog_entries_bulk(self, db: SessionDep, catalog_entry_identifiers: List[str]) -> None:
        """CatalogEntry들을 메타데이터와 컬럼 관계 기반으로 벌크 변환."""
        if not catalog_entry_identifiers:
            logging.warning("Empty catalog_entry_identifiers in bulk transform.")
            return

        catalog_entries = self.catalog_entry_service.get_catalog_entries_by_identifier(db, catalog_entry_identifiers)
        metadata_entries = self.metadata_entry_service.select_metadata_bulk(db, catalog_entry_identifiers)

        all_relations = self.column_relation_service.get_relations_by_metadata_columns(
            db, list(set(metadata_entry.metadata_schema for metadata_entry in metadata_entries))
        )

        catalog_entry_updates = []

        for catalog_entry in catalog_entries:
            current_metadata = [e for e in metadata_entries if e.metadata_id == catalog_entry.identifier]

            # Apply transformation
            catalog_entry_update = CatalogEntryUpdate()
            self._apply_metadata_to_update(catalog_entry_update, current_metadata, all_relations)

            # Prepare update dict if any fields were set
            if any(getattr(catalog_entry_update, field) is not None for field in CatalogEntryUpdate.model_fields):
                update_dict = catalog_entry_update.model_dump(exclude_none=True)
                update_dict["id"] = catalog_entry.id
                catalog_entry_updates.append(update_dict)

        if catalog_entry_updates:
            self.catalog_entry_service.update_catalog_entry_bulk(db, catalog_entry_updates)
