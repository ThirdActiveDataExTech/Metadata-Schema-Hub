import io
import json
import pathlib
from typing import Optional

import xmltodict
from fastapi import APIRouter, Depends, File, Path, UploadFile, Query
from starlette.responses import StreamingResponse

from app.dependencies import SessionDep
from app.schemas.response import APIResponseModel
from app.src.catalog_entry.exceptions import CatalogEntryServiceError
from app.src.catalog_entry.model import CatalogEntryCreate
from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.catalog_entry.service import CatalogEntryService, CatalogEntryTransformService
from app.src.column_relation.repository import ColumnRelationRepository
from app.src.metadata_entry.model import MetadataBase
from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.service import MetadataEntryService

router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_catalog_entry_service(repository=Depends(CatalogEntryRepository)):
    """Repository dependency injection."""
    return CatalogEntryService(repository)


def get_metadata_entry_service(repository=Depends(MetadataEntryRepository)):
    """Repository dependency injection."""
    return MetadataEntryService(repository)


def get_catalog_entry_transform_service(
        catalog_entry_repository=Depends(CatalogEntryRepository),
        column_relation_repository=Depends(ColumnRelationRepository)
):
    """Repository dependency injection."""
    return CatalogEntryTransformService(catalog_entry_repository, column_relation_repository)


@router.get("/entry/{catalog_entry_id}")
async def read_catalog(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    catalog_entry_id: int = Path(description="조회할 카탈로그 엔트리의 ID", title="Catalog Entry ID", example=31),
):
    catalog_entry = service.get_raw_metadata(db=session, catalog_entry_id=catalog_entry_id)
    return APIResponseModel(result=catalog_entry, description="Entry Found.")


@router.get("/")
async def search_catalog(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    query: Optional[str] = Query(None, description="제목, 설명에서 검색할 텍스트, LIKE"),
    keyword: Optional[str] = Query(None, description="키워드 필터, EXACT"),
    limit: int = Query(10, description="조회 제한 개수", ge=1, le=1000)
):
    """메타데이터 카탈로그 검색 (query, keyword만 지원)"""

    # 검색 조건 존재 여부 확인
    has_search_params = bool(query or keyword)

    if has_search_params:
        # 검색 수행
        result = service.search_catalog(
            db=session,
            query=query,
            keyword=keyword
        )
        description = f"검색 완료. 총 {len(result)}건 조회"
    else:
        # 전체 목록 조회
        result = service.list_catalog(db=session, limit=limit)
        # limit 적용 (서비스에서 지원하지 않는 경우 슬라이싱)
        if len(result) > limit:
            result = result[:limit]
        description = f"목록 조회 완료. 총 {len(result)}건 조회"

    return APIResponseModel(
        result=result,
        description=description
    )


@router.post("/import/metadata")
async def import_metadata(
    session: SessionDep,
    metadata_entry_service: MetadataEntryService = Depends(get_metadata_entry_service),
    catalog_entry_service: CatalogEntryService = Depends(get_catalog_entry_service),
    catalog_entry_transform_service: CatalogEntryTransformService = Depends(get_catalog_entry_transform_service),
    file: UploadFile = File(description="Json 직렬화 가능한 메타데이터 파일"),
):
    # TODO: 3 개의 TX 가 수행됨, create_catalog_entry TX 가 성공되면 이후는 retry 가능하나, retry 로직 없음.
    extension_to_type = {
        ".json": "json",
        ".jsonl": "json",
        ".jsonld": "json",
        ".xml": "xml",
        ".rdf": "xml",
    }

    type_functions = {
        "json": {
            "serializer": json.loads,
            "parser": metadata_entry_service.create_from_json,
        },
        "xml": {
            "serializer": xmltodict.parse,
            "parser": metadata_entry_service.create_from_xml,
        }
    }

    if not file.filename:
        raise CatalogEntryServiceError(message="파일 업로드가 필요합니다.")

    content = await file.read()
    extension = pathlib.Path(file.filename).suffix.lower()
    file_type = extension_to_type.get(extension, None)
    if not file_type:
        raise CatalogEntryServiceError(message=f"확장자 `{extension}` 는 지원하지 않는 형식입니다.")

    serialized_content = type_functions[file_type]["serializer"](content)

    catalog_entry_create = CatalogEntryCreate(raw_metadata=serialized_content)
    catalog_entry = catalog_entry_service.create_catalog_entry(db=session, catalog_entry_create=catalog_entry_create)

    del serialized_content

    parsed_data = type_functions[file_type]["parser"](db=session, metadata_id=catalog_entry.identifier, data=content)

    del content

    metadata_entries = [MetadataBase(metadata_schema=data.metadata_schema, value=data.value) for data in parsed_data]

    del parsed_data

    result = catalog_entry_transform_service.update_catalog_entry_from_metadata_and_relation(
        session,
        catalog_entry.id,
        metadata_entries
    )

    return APIResponseModel(result=result, description="Metadata import 및 변환 완료")


@router.get("/export/csv")
async def export_database(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    limit: int = 100
):
    csv_stream = service.export_to_csv_stream(session, limit)
    return StreamingResponse(
        io.StringIO(csv_stream.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=catalog_entries.csv"}
    )
