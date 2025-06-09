import io
import json
import os
import tempfile
from typing import List, Optional

import xmltodict
from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, Query
from starlette.responses import StreamingResponse

from app.dependencies import SessionDep
from app.schemas.catalog_entry import CatalogEntryCreate
from app.schemas.metadata_entry import MetadataBase
from app.schemas.response import APIResponseModel
from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.catalog_entry.service import CatalogEntryService, CatalogEntryTransformService
from app.src.column_relation.repository import ColumnRelationRepository
from app.src.dcat.dcat_processor import parse_dcat_xml
from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.service import MetadataEntryService
from app.src.schema_org.schema_org_processor import parse_schema_org_json

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
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일 업로드 필요")

    content = await file.read()

    parsed_data = None
    serialized_content = None

    if file.filename.endswith((".json", ".jsonld")):
        parsed_data = metadata_entry_service.create_from_json(session, content)
        serialized_content = json.loads(content)

    if file.filename.endswith((".xml", ".rdf")):
        parsed_data = metadata_entry_service.create_from_xml(session, content)
        serialized_content = xmltodict.parse(content)

    if not parsed_data or not serialized_content:
        raise HTTPException(status_code=400, detail="지원하지 않는 형식입니다.")

    # 같은 metadata 에서 생성된 parsed_data 들의 메타 컬럼(metadata_id ...) 모두 같은 값을 가짐
    catalog_entry_create = CatalogEntryCreate(identifier=parsed_data[0].metadata_id, raw_metadata=serialized_content)
    catalog_entry = catalog_entry_service.create_catalog_entry(db=session, catalog_entry_create=catalog_entry_create)

    metadata_entries = [MetadataBase(metadata_schema=data.metadata_schema, value=data.value) for data in parsed_data]

    result = catalog_entry_transform_service.update_catalog_entry_from_metadata_and_relation(
        session,
        catalog_entry.id,
        metadata_entries
    )

    return APIResponseModel(result=result, description="Metadata import 및 변환 완료")


@router.post("/import/schema-org")
async def import_schema_org(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    file: UploadFile = File(description="Schema.org JSON 형식의 메타데이터 파일", media_type="application/json"),
):
    """Schema.org JSON 파일을 업로드 후 카탈로그에 저장."""
    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".json", ".jsonld")):
        raise HTTPException(status_code=400, detail="JSON 파일만 업로드 가능")

    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        parsed_data = parse_schema_org_json(temp_file_path)
        imported_data = service.import_to_database(session, parsed_data)

        return APIResponseModel(result=imported_data, description="Schema.org JSON import 완료")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 파싱 실패: {str(e)}")

    finally:
        # 임시 파일 정리
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@router.post("/import/dcat")
async def import_dcat(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    file: UploadFile = File(description="DCAT XML/RDF 형식의 메타데이터 파일", media_type="application/xml"),
):
    """DCAT XML 파일을 업로드하여 파싱된 메타데이터를 반환"""

    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".xml", ".rdf")):
        raise HTTPException(status_code=400, detail="XML 또는 RDF 파일만 업로드 가능")

    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        parsed_data = parse_dcat_xml(temp_file_path)
        imported_data = service.import_to_database(session, parsed_data)

        return APIResponseModel(result=imported_data, description="DCAT XML 파일 파싱 완료")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 파싱 실패: {str(e)}")

    finally:
        # 임시 파일 정리
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


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


async def _bulk_import_files(
    session: SessionDep,
    service: CatalogEntryService,
    files: List[UploadFile],
    valid_extensions: tuple,
    parse_func,
    import_type: str
):
    """공통 bulk import 처리"""
    if not files:
        raise HTTPException(status_code=400, detail="최소 1개 파일 필요")

    processed_files = []
    failed_files = []
    temp_file_paths = []

    try:
        all_parsed_data = []

        for file in files:
            if not file.filename or not file.filename.endswith(valid_extensions):
                failed_files.append({
                    "filename": file.filename,
                    "error": f"{' 또는 '.join(valid_extensions)} 파일만 업로드 가능"
                })
                continue

            try:
                # 파일 확장자 추출
                file_suffix = os.path.splitext(file.filename)[1]

                with tempfile.NamedTemporaryFile(mode="wb", suffix=file_suffix, delete=False) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                    temp_file_paths.append(temp_file_path)

                parsed_data = parse_func(temp_file_path)
                all_parsed_data.append(parsed_data)
                processed_files.append({"filename": file.filename, "status": "success"})

            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "error": f"파일 파싱 실패: {str(e)}"
                })

        imported_data = []
        if all_parsed_data:
            imported_data = service.insert_data(session, all_parsed_data)

        result = APIResponseModel(
            result={
                "total_files": len(files),
                "processed_files": len(processed_files),
                "failed_files": len(failed_files),
                "imported_records": len(imported_data),
                "processed_list": processed_files,
                "failed_list": failed_files
            },
            description=f"{import_type} bulk import 완료"
        )

    except Exception as e:
        # 예상치 못한 에러 처리
        raise HTTPException(status_code=500, detail=f"bulk import 실패: {str(e)}")

    finally:
        for temp_path in temp_file_paths:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    return result


@router.post("/import/schema-org/bulk")
async def import_schema_org_bulk(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    files: List[UploadFile] = File(description="Schema.org JSON 형식의 메타데이터 파일들"),
):
    """여러 Schema.org JSON 파일을 업로드하여 카탈로그에 저장"""
    return await _bulk_import_files(
        session, service, files,
        (".json", ".jsonld"), parse_schema_org_json, "Schema.org JSON"
    )


@router.post("/import/dcat/bulk")
async def import_dcat_bulk(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    files: List[UploadFile] = File(description="DCAT XML/RDF 형식의 메타데이터 파일들"),
):
    """여러 DCAT XML 파일을 업로드하여 카탈로그에 저장"""
    return await _bulk_import_files(
        session, service, files,
        (".xml", ".rdf"), parse_dcat_xml, "DCAT XML"
    )
