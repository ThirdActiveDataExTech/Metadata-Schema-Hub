import logging
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

from app.dependencies import SessionDep
from app.src.catalog_entry.model import CatalogEntry, CatalogEntrySummary, CatalogEntryUpdate
from app.src.catalog_entry.service import CatalogEntryService
from app.src.column_relation.model import ColumnRelation
from app.src.column_relation.service import ColumnRelationService
from app.src.file_converter.file_handler import MetadataFile, process_metadata_file, process_metadata_files
from app.src.metadata_entry.model import MetadataBase, MetadataCreate
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

    def _set_catalog_entry_fields(
        self,
        catalog_entry: CatalogEntry,
        metadata_bases: List[MetadataBase],
        related_relations: List[ColumnRelation],
        preserve_existing: bool = False,
    ) -> CatalogEntry:
        catalog_entry_update = CatalogEntryUpdate()
        processed_columns = set()

        if preserve_existing:
            for field in catalog_entry.model_fields:
                catalog_entry_update.set_field(field, getattr(catalog_entry, field))
                processed_columns.add(field)

        metadata_schema_dict = {item.metadata_schema: item.value for item in metadata_bases}

        for relation in related_relations:
            # 이미 처리된 catalog_column은 스킵 (highest correlation 유지)
            if relation.catalog_column in processed_columns:
                continue

            metadata_value = metadata_schema_dict.get(relation.metadata_column)
            if metadata_value and relation.catalog_column in catalog_entry_update.model_fields:
                catalog_entry_update.set_field(relation.catalog_column, metadata_value)
                processed_columns.add(relation.catalog_column)

        return catalog_entry_update.apply_to_catalog_entry(catalog_entry=catalog_entry)

    def create_metadata_catalog_entry_from_metadata(
        self,
        db: SessionDep,
        file: MetadataFile,
    ) -> CatalogEntry:
        """메타데이터 파일을 처리하여 CatalogEntry 생성."""
        # TODO: unused method
        serialized_content, metadata_bases = process_metadata_file(file)
        ingested_at = datetime.now()

        metadata_create = MetadataCreate(metadata_bases=metadata_bases, ingested_at=ingested_at)
        catalog_entry = CatalogEntry(
            identifier=metadata_create.metadata_id,
            raw_metadata=serialized_content,
            ingested_at=ingested_at,
        )

        with db.begin():
            related_relations = self.column_relation_service.get_relations_by_metadata_columns(
                db=db,
                metadata_columns=[metadata_base.metadata_schema for metadata_base in metadata_bases],
            )

            catalog_entry = self._set_catalog_entry_fields(
                catalog_entry=catalog_entry,
                metadata_bases=metadata_bases,
                related_relations=related_relations,
                preserve_existing=False,  # 새로 생성하므로 기존 필드 유지 안함
            )

            self.metadata_entry_service.create(db=db, metadata_create=metadata_create)
            self.catalog_entry_service.create_catalog_entry(
                db=db,
                catalog_entry=catalog_entry,
            )

        return self.catalog_entry_service.get_catalog_entry_by_identifier(db, catalog_entry.identifier)

    def create_metadata_catalog_entries_from_metadatas(
        self,
        db: SessionDep,
        files: List[MetadataFile],
    ) -> Tuple[List[CatalogEntrySummary], List[Dict[str, str]]]:
        """여러 메타데이터 파일을 처리하여 CatalogEntry 리스트 생성."""
        # TODO: unused method
        processed_metadatas, errors = process_metadata_files(files)
        if not processed_metadatas:
            logging.warning("Empty files in bulk transform.")
            return [], errors

        ingested_at = datetime.now()

        iterrables = []
        metadata_schemas: Iterable[str] = set()
        for serialized_content, metadata_bases in processed_metadatas:
            metadata_create = MetadataCreate(metadata_bases=metadata_bases, ingested_at=ingested_at)
            catalog_entry = CatalogEntry(
                identifier=metadata_create.metadata_id,
                raw_metadata=serialized_content,
                ingested_at=ingested_at,
            )
            iterrables.append((catalog_entry, metadata_create))
            metadata_schemas.update(e.metadata_schema for e in metadata_bases)

        with db.begin():
            related_relations = self.column_relation_service.get_relations_by_metadata_columns(
                db=db,
                metadata_columns=metadata_schemas,
            )

            for catalog_entry, metadata_create in iterrables:
                catalog_entry = self._set_catalog_entry_fields(
                    catalog_entry=catalog_entry,
                    metadata_bases=metadata_create.metadata_bases,
                    related_relations=related_relations,
                    preserve_existing=False,
                )

            self.metadata_entry_service.create_bulk(
                db, metadata_create_list=[metadata_create for _, metadata_create in iterrables]
            )
            self.catalog_entry_service.create_catalog_entry_bulk(
                db, catalog_entries=[entry.model_dump() for entry, _ in iterrables]
            )

        return self.catalog_entry_service.get_catalog_entry_summary_by_identifier(
            db, [entry.identifier for entry, _ in iterrables]
        ), errors

    def update_catalog_entry_from_metadata_and_relation(
        self,
        db: SessionDep,
        catalog_entry_id: int,
    ) -> CatalogEntry:
        """CatalogEntry 를 메타데이터와 컬럼 관계 기반으로 매핑함."""
        catalog_entry = self.catalog_entry_service.get_catalog_entry(db, catalog_entry_id)

        metadata_entries = self.metadata_entry_service.select_metadata(db, catalog_entry.identifier)
        metadata_dict = {item.metadata_schema: item.value for item in metadata_entries}

        all_relations = self.column_relation_service.get_relations_by_metadata_columns(db, list(metadata_dict.keys()))

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
        self, db: SessionDep, catalog_entry_identifiers: List[str]
    ) -> None:
        """CatalogEntry 를 메타데이터와 컬럼 관계 기반으로 매핑함."""
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
