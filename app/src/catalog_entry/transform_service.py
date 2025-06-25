import logging
from typing import List

from app.dependencies import SessionDep
from app.src.catalog_entry.model import CatalogEntry, CatalogEntryUpdate
from app.src.catalog_entry.service import CatalogEntryService
from app.src.column_relation.service import ColumnRelationService
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

    def update_catalog_entry_from_metadata_and_relation(
            self,
            db: SessionDep,
            catalog_entry_id: int,
    ) -> CatalogEntry:
        """CatalogEntry 를 메타데이터와 컬럼 관계 기반으로 매핑함."""
        catalog_entry = self.catalog_entry_service.get_catalog_entry(db, catalog_entry_id)

        metadata_entries = self.metadata_entry_service.select_metadata(db, catalog_entry.identifier)
        metadata_dict = {item.metadata_schema: item.value for item in metadata_entries}

        all_relations = self.column_relation_service.get_relations_by_metadata_columns(
            db,
            list(metadata_dict.keys())
        )

        catalog_entry_update = CatalogEntryUpdate()
        processed_columns = set()  # 이미 처리된 catalog_column 추적

        for relation in all_relations:
            # 이미 처리된 catalog_column은 스킵 (highest correlation 유지)
            if relation.catalog_column in processed_columns:
                continue

            metadata_value = metadata_dict.get(relation.metadata_column)
            if metadata_value and relation.catalog_column in catalog_entry_update.model_fields:
                catalog_entry_update.set_field(relation.catalog_column, metadata_value)
                processed_columns.add(relation.catalog_column)

        return self.catalog_entry_service.update_catalog_entry(db, catalog_entry.id, catalog_entry_update)

    def update_catalog_entry_from_metadata_and_relation_bulk(
            self,
            db: SessionDep,
            catalog_entry_identifiers: List[str]
    ) -> None:
        """CatalogEntry 를 메타데이터와 컬럼 관계 기반으로 매핑함."""
        if not catalog_entry_identifiers:
            logging.warning("Empty catalog_entry_identifiers in bulk transform.")
            return

        with db.begin():
            catalog_entries = self.catalog_entry_service.get_catalog_entries_by_identifier(db,
                                                                                           catalog_entry_identifiers)
            metadata_entries = self.metadata_entry_service.select_metadata_bulk(db, catalog_entry_identifiers)

            all_relations = self.column_relation_service.get_relations_by_metadata_columns(
                db,
                list(set(metadata_entry.metadata_schema for metadata_entry in metadata_entries))
            )

            catalog_entry_updates = []

            for catalog_entry in catalog_entries:
                current_schema = [e for e in metadata_entries if e.metadata_id == catalog_entry.identifier]
                metadata_dict = {item.metadata_schema: item.value for item in current_schema}
                current_relations = [r for r in all_relations if r.metadata_column in metadata_dict.keys()]

                catalog_entry_update = CatalogEntryUpdate()
                processed_columns = set()
                for relation in current_relations:
                    # 이미 처리된 catalog_column은 스킵 (highest correlation 유지)
                    if relation.catalog_column in processed_columns:
                        continue

                    metadata_value = metadata_dict.get(relation.metadata_column)
                    if metadata_value and relation.catalog_column in catalog_entry_update.model_fields:
                        catalog_entry_update.set_field(relation.catalog_column, metadata_value)
                        processed_columns.add(relation.catalog_column)

                update_mapping = catalog_entry_update.model_dump_for_update()
                if update_mapping:
                    update_mapping["id"] = catalog_entry.id
                    catalog_entry_updates.append(update_mapping)

            self.catalog_entry_service.update_catalog_entry_bulk(db, catalog_entry_updates)
