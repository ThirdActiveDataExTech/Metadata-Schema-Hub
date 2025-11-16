import json
import pathlib
from collections import defaultdict
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile
from pydantic import Json

from app.config import settings
from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.catalog_entry.service import CatalogEntryService
from app.src.column_relation.repository import ColumnRelationRepository
from app.src.column_relation.service import ColumnRelationService
from app.src.file_converter.file_handler import MetadataFile, process_metadata_file, process_metadata_files
from app.src.file_converter.json_converter import JsonConverter
from app.src.file_converter.xml_converter import LxmlConverter
from app.src.metadata_entry.exceptions import (
    MetadataEntryFileNotFoundError,
    MetadataEntryInvalidFormatError,
    MetadataEntryNotSupportedTypeError,
    MetadataEntryTooManyFileError,
)
from app.src.metadata_entry.model import MetadataCreate
from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.service import MetadataEntryService

router = APIRouter(prefix="/metadata", tags=["metadata"], route_class=ExceptionHandlingRoute)


def get_json_converter():
    """Converter dependency injection."""
    return JsonConverter()


def get_xml_converter():
    """Converter dependency injection."""
    return LxmlConverter()


def get_catalog_entry_service(repository=Depends(CatalogEntryRepository)):
    """Repository dependency injection."""
    return CatalogEntryService(repository)


def get_column_relation_service(repository=Depends(ColumnRelationRepository)):
    """Repository dependency injection."""
    return ColumnRelationService(repository)


def get_metadata_entry_service(repository=Depends(MetadataEntryRepository)):
    """Repository dependency injection."""
    return MetadataEntryService(repository)


@router.get("/entries")
async def search_metadata_entries(
    session: SessionDep,
    service: MetadataEntryService = Depends(get_metadata_entry_service),
    query: Optional[str] = Query(None, description="값, 스키마 텍스트 검색 (LIKE 패턴)"),
    schema: Optional[str] = Query(None, description="메타데이터 스키마 정확 일치 필터"),
    metadata_id: Optional[str] = Query(None, description="메타데이터 ID 정확 일치 필터"),
    limit: int = Query(10, description="검색 결과 제한 개수", ge=1, le=100),  # TODO: test 되지 않은 limit
):
    """메타데이터 엔트리 검색 (쿼리, 스키마, 메타데이터 ID 기반)"""

    # 검색 조건 존재 여부 확인
    has_search_params = bool(query or schema or metadata_id)

    if has_search_params:
        # 검색 수행
        result = service.search_metadata(db=session, query=query, schema=schema, metadata_id=metadata_id)
        description = f"검색 완료. 총 {len(result)}건 조회"
    else:
        # 전체 목록 조회
        result = service.list_metadata(db=session, limit=limit)
        # limit 적용
        if len(result) > limit:
            result = result[:limit]
        description = f"목록 조회 완료. 총 {len(result)}건 조회"

    return APIResponseModel(result=result, description=description)


@router.post("/convert/schema-org")
async def convert_schema_org_metadata(
    converter: JsonConverter = Depends(get_json_converter),
    file: UploadFile = File(description="Schema.org JSON-LD 메타데이터 파일", media_type="application/json"),
):
    """Schema.org JSON-LD 형식 메타데이터를 테이블 구조로 변환"""
    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".json", ".jsonld")):
        extension = pathlib.Path(file.filename).suffix.lower()
        raise MetadataEntryNotSupportedTypeError(type=extension)

    content = await file.read()
    parsed_data = converter.convert_to_metadata_bases(content)

    return APIResponseModel(result=parsed_data, description="Schema.org JSON import 완료")


@router.post("/convert/dcat")
async def convert_dcat_metadata(
    converter: LxmlConverter = Depends(get_xml_converter),
    file: UploadFile = File(description="DCAT RDF/XML 메타데이터 파일", media_type="application/xml"),
):
    """DCAT RDF/XML 형식 메타데이터를 테이블 구조로 변환"""

    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".xml", ".rdf")):
        extension = pathlib.Path(file.filename).suffix.lower()
        raise MetadataEntryNotSupportedTypeError(type=extension)

    content = await file.read()
    parsed_data = converter.convert_to_metadata_bases(content)

    return APIResponseModel(result=parsed_data, description="DCAT XML 파일 파싱 완료")


@router.post("/ingest/metadata")
async def ingest_metadata(
    session: SessionDep,
    metadata_service: MetadataEntryService = Depends(get_metadata_entry_service),
    catalog_service: CatalogEntryService = Depends(get_catalog_entry_service),
    file: UploadFile = File(description="메타데이터 파일"),
):
    """메타데이터를 테이블 구조로 변환하여 수집"""
    metadata_file = MetadataFile(filename=file.filename, content=await file.read())
    try:
        serialized_content, metadata_bases = process_metadata_file(metadata_file)
    except ValueError as e:
        raise MetadataEntryNotSupportedTypeError(type=metadata_file.get_extension(), result=str(e))

    catalog_result = catalog_service.create_catalog_entry(
        db=session, catalog_entry=CatalogEntry(raw_metadata=serialized_content)
    )

    metadata_result = metadata_service.create(
        db=session,
        metadata_create=MetadataCreate(
            metadata_id=catalog_result.identifier, metadata_bases=metadata_bases, ingested_at=catalog_result.ingested_at
        ),
    )

    return APIResponseModel(
        result={"catalog_result": catalog_result, "metadata_result": metadata_result},
        description="메타데이터 수집 완료",
    )


@router.post("/ingest/metadata/bulk")
async def ingest_metadata_bulk(
    session: SessionDep,
    metadata_service: MetadataEntryService = Depends(get_metadata_entry_service),
    catalog_service: CatalogEntryService = Depends(get_catalog_entry_service),
    files: List[UploadFile] = File(description="메타데이터 파일들"),
):
    """여러 메타데이터를 테이블 구조로 변환하여 수집"""
    if not files:
        raise MetadataEntryFileNotFoundError(message="최소 1개 이상의 파일이 필요")
    if len(files) > settings.MAXIMUM_INGESTION_LIMIT:
        raise MetadataEntryTooManyFileError(message=f"최대 {settings.MAXIMUM_INGESTION_LIMIT}개 파일까지 처리 가능")

    metadata_files = [MetadataFile(filename=file.filename, content=await file.read()) for file in files]

    processed_metadatas, errors = process_metadata_files(metadata_files)
    if not processed_metadatas:
        return APIResponseModel(
            result={"processed_count": 0, "errors": errors},
            description="처리된 메타데이터가 없습니다",
        )

    ingested_at = datetime.now()

    iterables: List[Tuple[CatalogEntry, MetadataCreate]] = []
    for serialized_content, metadata_bases in processed_metadatas:
        metadata_create = MetadataCreate(metadata_bases=metadata_bases, ingested_at=ingested_at)
        catalog_entry = CatalogEntry(
            identifier=metadata_create.metadata_id,
            raw_metadata=serialized_content,
            ingested_at=ingested_at,
        )
        iterables.append((catalog_entry, metadata_create))
    catalog_service.create_catalog_entry_bulk(db=session, catalog_entries=[entry.model_dump() for entry, _ in iterables])
    metadata_service.create_bulk(db=session, metadata_create_list=[metadata_create for _, metadata_create in iterables])

    return APIResponseModel(
        result={
            "processed_count": len(iterables),
            "catalog_result": [entry for entry, _ in iterables],
            "metadata_result": [metadata_create for _, metadata_create in iterables],
            "errors": errors,
        },
        description="메타데이터 벌크 수집 완료",
    )


@router.get("/{metadata_id}")
async def get_metadata_entry(
    session: SessionDep,
    service: MetadataEntryService = Depends(get_metadata_entry_service),
    metadata_id: str = Path(
        description="메타데이터 엔트리 UUID",
        example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
        regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",  # UUID 검증 정규식
    ),
):
    """UUID로 파싱된 메타데이터 엔트리 조회"""
    result = service.select_metadata(session, metadata_id=metadata_id)

    return APIResponseModel(result=result, description="Metadata Found.")


@router.post("/preview")
async def preview_metadata(
    session: SessionDep,
    relation_service: ColumnRelationService = Depends(get_column_relation_service),
    file: UploadFile = File(description="메타데이터 파일"),
):
    """메타데이터를 json 으로 변환하여 preview"""
    metadata_file = MetadataFile(filename=file.filename, content=await file.read())

    try:
        _, metadata_bases = process_metadata_file(metadata_file)
    except ValueError as e:
        raise MetadataEntryNotSupportedTypeError(type=metadata_file.get_extension(), result=str(e))

    metadata_schemas = [base.metadata_schema for base in metadata_bases]
    relations = relation_service.get_relations_by_metadata_columns(session, metadata_schemas)

    metadata_candidates = defaultdict(list)
    for relation in relations:
        metadata_candidates[relation.metadata_column].append(
            {
                "catalog_column": relation.catalog_column,
                "correlation": relation.correlation,
            }
        )

    best_matches = {
        meta_col: max(candidates, key=lambda x: x["correlation"])["catalog_column"]
        for meta_col, candidates in metadata_candidates.items()
        if candidates
    }

    schema_to_value = {base.metadata_schema: base.value for base in metadata_bases}

    metadata = {best_matches[schema]: schema_to_value[schema] for schema in best_matches if schema in schema_to_value}

    untyped = {
        base.metadata_schema: base.value for base in metadata_bases if base.metadata_schema not in metadata_candidates
    }

    return APIResponseModel(
        result={
            "metadata": metadata,
            "metadata_candidates": metadata_candidates,
            "untyped": untyped,
        },
        description="메타데이터 미리보기 생성 완료.",
    )


@router.post("/form")
async def ingest_form(
    session: SessionDep,
    metadata_service: MetadataEntryService = Depends(get_metadata_entry_service),
    catalog_service: CatalogEntryService = Depends(get_catalog_entry_service),
    json_converter: JsonConverter = Depends(get_json_converter),
    metadata_form: str = Form(description="메타데이터 Json"),
):
    """메타데이터를 테이블 구조로 변환하여 수집"""
    try:
        serialized_content = json.loads(metadata_form)
    except json.JSONDecodeError as e:
        raise MetadataEntryInvalidFormatError(format_type="JSON", message=str(e))

    metadata_bases = json_converter.convert_to_metadata_bases(metadata_form)

    catalog_result = catalog_service.create_catalog_entry(
        db=session, catalog_entry=CatalogEntry(raw_metadata=serialized_content)
    )

    metadata_result = metadata_service.create(
        db=session,
        metadata_create=MetadataCreate(
            metadata_id=catalog_result.identifier, metadata_bases=metadata_bases, ingested_at=catalog_result.ingested_at
        ),
    )

    return APIResponseModel(
        result={"catalog_result": catalog_result, "metadata_result": metadata_result},
        description="메타데이터 수집 완료",
    )
