from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Path

from app.dependencies import SessionDep
from app.schemas.response import APIResponseModel
from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.service import MetadataEntryService

router = APIRouter(prefix="/metadata", tags=["metadata"])


def get_metadata_entry_service(repository=Depends(MetadataEntryRepository)):
    """Repository dependency injection."""
    return MetadataEntryService(repository)


@router.post("/import/schema-org")
async def import_schema_org(
        session: SessionDep,
        service: MetadataEntryService = Depends(get_metadata_entry_service),
        file: UploadFile = File(description="Schema.org JSON 형식의 메타데이터 파일", media_type="application/json"),
):
    """Schema.org JSON 파일을 업로드 후 카탈로그에 저장."""
    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".json", ".jsonld")):
        raise HTTPException(status_code=400, detail="JSON 파일만 업로드 가능")

    content = await file.read()
    parsed_data = service.create_from_json(session, content)

    return APIResponseModel(result=parsed_data, description="Schema.org JSON import 완료")


@router.post("/import/dcat")
async def import_dcat(
        session: SessionDep,
        service: MetadataEntryService = Depends(get_metadata_entry_service),
        file: UploadFile = File(description="DCAT XML/RDF 형식의 메타데이터 파일", media_type="application/xml"),
):
    """DCAT XML 파일을 업로드하여 파싱된 메타데이터를 반환"""

    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".xml", ".rdf")):
        raise HTTPException(status_code=400, detail="XML 또는 RDF 파일만 업로드 가능")

    content = await file.read()
    parsed_data = service.create_from_xml(session, content)

    return APIResponseModel(result=parsed_data, description="DCAT XML 파일 파싱 완료")


@router.get("/select/{metadata_id}")
async def select_metadata(
        session: SessionDep,
        service: MetadataEntryService = Depends(get_metadata_entry_service),
        metadata_id: str = Path(
            description="조회할 메타데이터 엔트리의 ID, UUID",
            title="Metadata Entry ID",
            example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd"
        ),
):
    """Select metadata."""
    result = service.select_metadata(session, metadata_id=metadata_id)

    return APIResponseModel(result=result, description="Metadata Found.")
