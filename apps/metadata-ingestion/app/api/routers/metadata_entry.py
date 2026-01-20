import pathlib
from collections import defaultdict
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, File, Path, Query, UploadFile

from app.config import settings
from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.catalog_entry.dependencies import CatalogEntryServiceDep
from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry.schemas import MetadataCreateSummary
from app.src.column_relation.dependencies import ColumnRelationServiceDep
from app.src.file_converter.dependencies import JsonConverterDep, XmlConverterDep
from app.src.file_converter.file_handler import MetadataFile, process_metadata_file, process_metadata_files
from app.src.metadata_entry.dependencies import MetadataEntryServiceDep
from app.src.metadata_entry.examples import METADATA_FORM_EXAMPLES
from app.src.metadata_entry.exceptions import (
    MetadataEntryFileNotFoundError,
    MetadataEntryNotSupportedTypeError,
    MetadataEntryTooManyFileError,
)
from app.src.metadata_entry.model import MetadataCreate
from app.src.metadata_entry.schemas import (
    FilterKeyResponse,
    IngestBulkResponse,
    IngestResponse,
    MetadataBaseResponse,
    MetadataEntryResponse,
    PreviewResponse,
)
from app.src.workflow.dependencies import CatalogEntryTransformServiceDep

router = APIRouter(prefix="/metadata", tags=["metadata"], route_class=ExceptionHandlingRoute)


@router.get(
    "/filters/schemas",
    summary="메타데이터 필터 스키마 목록 조회",
    response_model=APIResponseModel[FilterKeyResponse],
)
async def get_metadata_filter_keys(
    session: SessionDep,
    service: MetadataEntryServiceDep,
):
    """메타데이터 검색 시 사용 가능한 필터 스키마 목록을 조회합니다.

    DB에 저장된 모든 고유한 `metadata_schema` 값을 반환합니다.
    이 목록은 메타데이터 필터 UI 구성이나 검색 옵션 제공에 활용됩니다."""
    filters = service.get_all_metadata_schemas(db=session)
    return APIResponseModel(result={"filters": filters}, description=f"필터 스키마 목록 조회 완료. 총 {len(filters)}개")


@router.get(
    "/entries",
    summary="메타데이터 엔트리 검색 및 목록 조회",
    response_model=APIResponseModel[List[Dict[str, Any]] | List[MetadataEntryResponse]],
)
async def search_metadata_entries(
    session: SessionDep,
    service: MetadataEntryServiceDep,
    query: Annotated[
        Optional[str],
        Query(
            title="검색어",
            description="값 또는 스키마명에서 텍스트 검색 (LIKE 패턴)",
            openapi_examples={
                "simple": {"summary": "간단한 검색", "value": "title"},
                "detailed": {"summary": "상세 검색", "value": "description"},
            },
        ),
    ] = None,
    schema: Annotated[
        Optional[str],
        Query(
            title="스키마명",
            description="메타데이터 스키마명 정확 일치 필터",
            openapi_examples={
                "dct": {"summary": "Dublin Core Title", "value": "dct:title"},
                "schema_org": {"summary": "Schema.org Name", "value": "schema:name"},
            },
        ),
    ] = None,
    metadata_id: Annotated[
        Optional[str],
        Query(
            title="메타데이터 ID",
            description="메타데이터 ID(UUID) 정확 일치 필터",
            openapi_examples={
                "uuid_example": {
                    "summary": "UUID 예시",
                    "value": "18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
                },
            },
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            title="결과 제한",
            description="검색 결과 제한 개수",
            openapi_examples={
                "small": {"summary": "소량 조회", "value": 10},
                "large": {"summary": "대량 조회", "value": 50},
            },
        ),
    ] = 10,
):
    """메타데이터 엔트리를 검색하거나 전체 목록을 조회합니다.

    검색 조건(`query`, `schema`, `metadata_id`)이 제공되면 해당 조건으로 검색하고,
    조건이 없으면 전체 목록을 반환합니다.

    메타데이터는 원본 파일에서 추출된 `key-value` 쌍으로 저장되어 있으며,
    동일한 `metadata_id`를 가진 엔트리들은 하나의 원본 파일에서 추출된 것입니다.

    **사용 사례:**
    1. 전체 목록 조회: 조건 없이 호출
    2. 메타데이터 검색: `query`, `schema`, `metadata_id` 조건 제공
    3. 필터 value 조회: `schema`만 지정하여 특정 key의 value 목록 조회"""

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


@router.post(
    "/convert/schema-org",
    summary="Schema.org JSON-LD 변환",
    response_model=APIResponseModel[List[MetadataBaseResponse]],
    responses={
        400: {"description": "지원하지 않는 파일 확장자"},
        422: {"description": "JSON 파싱 실패"},
    },
)
async def convert_schema_org_metadata(
    converter: JsonConverterDep,
    file: UploadFile = File(
        title="메타데이터 파일",
        description="Schema.org JSON-LD 메타데이터 파일 (.json, .jsonld)",
        media_type="application/json",
    ),
):
    """Schema.org JSON-LD 형식의 메타데이터를 테이블 구조로 변환합니다.

    JSON-LD 파일을 파싱하여 key-value 쌍의 메타데이터 베이스 목록으로 변환합니다.
    이 API는 변환만 수행하며 데이터를 저장하지 않습니다.
    실제 수집을 위해서는 `POST /metadata/ingest/metadata` 엔드포인트를 사용하세요."""
    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".json", ".jsonld")):
        extension = pathlib.Path(file.filename).suffix.lower()
        raise MetadataEntryNotSupportedTypeError(type=extension)

    content = await file.read()
    parsed_data = converter.convert_to_metadata_bases(content)

    return APIResponseModel(result=parsed_data, description="Schema.org JSON import 완료")


@router.post(
    "/convert/dcat",
    summary="DCAT RDF/XML 변환",
    response_model=APIResponseModel[List[MetadataBaseResponse]],
    responses={
        400: {"description": "지원하지 않는 파일 확장자"},
        422: {"description": "XML 파싱 실패"},
    },
)
async def convert_dcat_metadata(
    converter: XmlConverterDep,
    file: UploadFile = File(
        title="메타데이터 파일",
        description="DCAT RDF/XML 메타데이터 파일 (.xml, .rdf)",
        media_type="application/xml",
    ),
):
    """DCAT RDF/XML 형식의 메타데이터를 테이블 구조로 변환합니다.

    RDF/XML 파일을 파싱하여 `key-value` 쌍의 메타데이터 베이스 목록으로 변환합니다.
    이 API는 변환만 수행하며 데이터를 저장하지 않습니다.
    실제 수집을 위해서는 `POST /metadata/ingest/metadata` 엔드포인트를 사용하세요."""

    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".xml", ".rdf")):
        extension = pathlib.Path(file.filename).suffix.lower()
        raise MetadataEntryNotSupportedTypeError(type=extension)

    content = await file.read()
    parsed_data = converter.convert_to_metadata_bases(content)

    return APIResponseModel(result=parsed_data, description="DCAT XML 파일 파싱 완료")


# TODO: draft 구조 변경


@router.post(
    "/ingest/metadata",
    summary="메타데이터 단일 수집",
    response_model=APIResponseModel[IngestResponse],
    responses={
        400: {"description": "지원하지 않는 파일 형식"},
        422: {"description": "파일 파싱 실패"},
    },
)
async def ingest_metadata(
    session: SessionDep,
    metadata_service: MetadataEntryServiceDep,
    catalog_service: CatalogEntryServiceDep,
    transform_service: CatalogEntryTransformServiceDep,
    file: UploadFile = File(
        title="메타데이터 파일",
        description="메타데이터 파일 (.json, .jsonld, .xml, .rdf - Schema.org 또는 DCAT 형식)",
    ),
):
    """메타데이터 파일을 수집하고 자동으로 카탈로그 엔트리로 변환합니다.

    업로드된 메타데이터 파일을 다음 단계로 처리합니다:
    1. 파일 형식 자동 감지 및 파싱
    2. `key-value` 구조로 분해하여 `metadata_entry` 테이블에 저장
    3. 원본 메타데이터를 포함한 `catalog_entry` 초안 생성
    4. 컬럼 관계 기반 자동 매핑을 통한 `catalog_entry` 갱신

    지원 형식: Schema.org JSON-LD (`.json`, `.jsonld`), DCAT RDF/XML (`.xml`, `.rdf`)"""
    metadata_file = MetadataFile(filename=file.filename, content=await file.read())
    try:
        serialized_content, metadata_bases = process_metadata_file(metadata_file)
    except ValueError as e:
        raise MetadataEntryNotSupportedTypeError(type=metadata_file.get_extension(), result=str(e))

    catalog_draft = catalog_service.create_catalog_entry(
        db=session, catalog_entry=CatalogEntry(raw_metadata=serialized_content)
    )

    metadata_result = metadata_service.create(
        db=session,
        metadata_create=MetadataCreate(
            metadata_id=catalog_draft.identifier, metadata_bases=metadata_bases, ingested_at=catalog_draft.ingested_at
        ),
    )

    catalog_result = transform_service.update_catalog_entry_from_metadata_and_relation(
        db=session, catalog_entry_id=catalog_draft.id
    )

    return APIResponseModel(
        result={"catalog_result": catalog_result, "metadata_result": metadata_result},
        description="메타데이터 수집 완료",
    )


@router.post(
    "/ingest/metadata/bulk",
    summary="메타데이터 대량 수집",
    response_model=APIResponseModel[IngestBulkResponse],
    responses={
        400: {"description": "파일이 없거나 개수 제한 초과"},
    },
)
async def ingest_metadata_bulk(
    session: SessionDep,
    metadata_service: MetadataEntryServiceDep,
    catalog_service: CatalogEntryServiceDep,
    transform_service: CatalogEntryTransformServiceDep,
    files: List[UploadFile] = File(
        title="메타데이터 파일 목록",
        description="메타데이터 파일 목록 (최대 100개, .json/.jsonld/.xml/.rdf/.zip)",
    ),
):
    """여러 메타데이터 파일을 한 번에 수집하고 카탈로그 엔트리로 변환합니다.

    다수의 메타데이터 파일을 효율적으로 처리하기 위한 벌크 수집 API입니다.
    각 파일은 독립적으로 처리되며, 일부 파일의 실패가 전체 처리를 중단하지 않습니다.

    처리 과정:
    1. 각 파일의 형식을 자동 감지하고 파싱
    2. 성공한 파일들을 일괄 처리하여 `metadata_entry` 저장
    3. `catalog_entry` 초안 일괄 생성
    4. 컬럼 관계 기반 자동 매핑 일괄 수행

    최대 100개 파일까지 동시 처리 가능하며, 일부 파일 실패 시에도 성공한 파일들은 정상 처리됩니다.
    에러 정보는 `result.errors`에 포함됩니다."""
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

    transform_service.update_catalog_entry_from_metadata_and_relation_bulk(
        db=session, catalog_entry_identifiers=[entry.identifier for entry, _ in iterables]
    )

    # DB에서 생성된 catalog entries 다시 조회 (id 포함)
    catalog_results = catalog_service.get_catalog_entries_by_identifier(
        db=session, catalog_entry_identifiers=[entry.identifier for entry, _ in iterables]
    )

    # MetadataCreateSummary 생성
    metadata_results = [
        MetadataCreateSummary(
            metadata_id=metadata_create.metadata_id,
            total_entries=len(metadata_create.metadata_bases),
            ingested_at=metadata_create.ingested_at,
        )
        for _, metadata_create in iterables
    ]

    return APIResponseModel(
        result={
            "processed_count": len(iterables),
            "catalog_result": catalog_results,
            "metadata_result": metadata_results,
            "errors": errors,
        },
        description="메타데이터 벌크 수집 완료",
    )


@router.get(
    "/{metadata_id}",
    summary="메타데이터 ID로 조회",
    response_model=APIResponseModel[List[MetadataEntryResponse]],
    responses={
        404: {"description": "해당 UUID의 메타데이터가 존재하지 않음"},
        422: {"description": "UUID 형식이 올바르지 않음"},
    },
)
async def get_metadata_entry(
    session: SessionDep,
    service: MetadataEntryServiceDep,
    metadata_id: str = Path(
        title="메타데이터 ID",
        description="메타데이터 엔트리의 고유 식별자 (UUID v4 형식)",
        example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    ),
):
    """UUID를 사용하여 특정 메타데이터 엔트리의 모든 `key-value` 쌍을 조회합니다.

    동일한 `metadata_id`를 가진 모든 메타데이터 엔트리를 반환합니다.
    하나의 원본 파일에서 추출된 모든 메타데이터 항목을 확인할 수 있습니다."""
    result = service.select_metadata(session, metadata_id=metadata_id)

    return APIResponseModel(result=result, description="Metadata Found.")


@router.post(
    "/preview",
    summary="메타데이터 미리보기",
    response_model=APIResponseModel[PreviewResponse],
    responses={
        400: {"description": "지원하지 않는 파일 형식"},
        422: {"description": "파일 파싱 실패"},
    },
)
async def preview_metadata(
    session: SessionDep,
    relation_service: ColumnRelationServiceDep,
    file: UploadFile = File(
        title="메타데이터 파일",
        description="미리보기할 메타데이터 파일 (.json, .jsonld, .xml, .rdf)",
    ),
):
    """메타데이터 파일의 구조와 매핑 후보를 수집 전에 미리 확인합니다.

    파일을 실제로 저장하지 않고, 다음 정보를 확인할 수 있습니다:
    1. 파싱된 메타데이터 구조 (`key-value` 쌍)
    2. 컬럼 관계 기반 자동 매핑 결과
    3. 각 메타데이터 스키마에 대한 매핑 후보 목록
    4. 매핑되지 않은 필드 목록

    이 API는 데이터를 저장하지 않습니다. 실제 수집을 위해서는 `POST /metadata/ingest/metadata`를 사용하세요.

    반환 정보:
    - `metadata`: 자동 매핑된 카탈로그 컬럼과 값
    - `metadata_candidates`: 각 메타데이터 스키마의 매핑 후보 목록 (연관성 점수 포함)
    - `untyped`: 매핑 후보가 없는 메타데이터 스키마와 값"""
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


@router.post(
    "/form",
    summary="JSON 폼 데이터 수집",
    response_model=APIResponseModel[IngestResponse],
    responses={
        400: {"description": "JSON 형식이 올바르지 않음"},
    },
)
async def ingest_form(
    session: SessionDep,
    metadata_service: MetadataEntryServiceDep,
    catalog_service: CatalogEntryServiceDep,
    transform_service: CatalogEntryTransformServiceDep,
    json_converter: JsonConverterDep,
    metadata_form: Annotated[
        Dict[str, Any],
        Body(
            title="메타데이터 JSON",
            description="JSON 형식의 메타데이터 (Schema.org, DCAT, 또는 사용자 정의 형식 지원)",
            media_type="application/json",
            openapi_examples=METADATA_FORM_EXAMPLES,
        ),
    ],
):
    """JSON 형식의 폼 데이터를 메타데이터로 수집합니다.

    파일 업로드 대신 JSON 객체를 직접 전송하여 메타데이터를 수집합니다.
    웹 폼이나 API 통합 시 유용한 엔드포인트입니다.

    처리 과정:
    1. JSON 객체 검증 및 변환
    2. `key-value` 구조로 분해하여 `metadata_entry` 저장
    3. `catalog_entry` 초안 생성
    4. 컬럼 관계 기반 자동 매핑 수행

    파일 업로드와 동일한 처리 과정을 거치며, 결과도 동일합니다."""
    serialized_content = metadata_form

    metadata_bases = json_converter.convert_to_metadata_bases(metadata_form)

    catalog_draft = catalog_service.create_catalog_entry(
        db=session, catalog_entry=CatalogEntry(raw_metadata=serialized_content)
    )

    metadata_result = metadata_service.create(
        db=session,
        metadata_create=MetadataCreate(
            metadata_id=catalog_draft.identifier, metadata_bases=metadata_bases, ingested_at=catalog_draft.ingested_at
        ),
    )

    catalog_result = transform_service.update_catalog_entry_from_metadata_and_relation(
        db=session, catalog_entry_id=catalog_draft.id
    )

    return APIResponseModel(
        result={"catalog_result": catalog_result, "metadata_result": metadata_result},
        description="메타데이터 수집 완료",
    )
