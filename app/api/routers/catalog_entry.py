"""
PUT, POST, GET 에 대한 다양한 API 예시를 작성해놨으니 참고해서 개발을 진행한다.
되도록이면 Swagger에서 API를 쉽게 파악하기 위해 API 및 Body, Path, Query에 대한 설명을 작성한다.
"""

import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile

from app.dependencies import SessionDep
from app.schemas.response import APIResponseModel
from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.catalog_entry.service import CatalogEntryService
from app.src.dcat.dcat_processor import parse_dcat_xml
from app.src.schema_org.schema_org_processor import parse_schema_org_json

router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_catalog_entry_service(repository=Depends(CatalogEntryRepository)):
    """Repository dependency injection."""
    return CatalogEntryService(repository)


@router.get("/{catalog_entry_id}")
async def read_catalog(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    catalog_entry_id: int = Path(description="조회할 카탈로그 엔트리의 ID", title="Catalog Entry ID", examples=[31]),
):
    catalog_entry = service.get_raw_metadata(db=session, catalog_entry_id=catalog_entry_id)
    return APIResponseModel(result=catalog_entry, description="Entry Found.")


@router.post("/schema-org")
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


@router.post("/dcat")
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
