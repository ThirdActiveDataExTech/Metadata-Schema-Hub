import pathlib

from fastapi import APIRouter, Depends, File, UploadFile, Path

from app.dependencies import SessionDep
from app.schemas.response import APIResponseModel
from app.src.metadata_entry.exceptions import MetadataEntryNotSupportedTypeError
from app.src.metadata_entry.json_converter import JsonConverter
from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.service import MetadataEntryService
from app.src.metadata_entry.xml_converter import LxmlConverter

router = APIRouter(prefix="/metadata", tags=["metadata"])


def get_json_converter():
    """Converter dependency injection."""
    return JsonConverter()


def get_xml_converter():
    """Converter dependency injection."""
    return LxmlConverter()


def get_metadata_entry_service(repository=Depends(MetadataEntryRepository)):
    """Repository dependency injection."""
    return MetadataEntryService(repository)


@router.post("/convert/schema-org")
async def convert_schema_org(
        converter: JsonConverter = Depends(get_json_converter),
        file: UploadFile = File(description="Schema.org JSON 형식의 메타데이터 파일", media_type="application/json"),
):
    """Schema.org JSON 파일을 파싱, 결과 반환."""
    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".json", ".jsonld")):
        extension = pathlib.Path(file.filename).suffix.lower()
        raise MetadataEntryNotSupportedTypeError(type=extension)

    content = await file.read()
    parsed_data = converter.convert_to_table(content)

    return APIResponseModel(result=parsed_data, description="Schema.org JSON import 완료")


@router.post("/convert/dcat")
async def convert_dcat(
        converter: LxmlConverter = Depends(get_xml_converter),
        file: UploadFile = File(description="DCAT XML/RDF 형식의 메타데이터 파일", media_type="application/xml"),
):
    """DCAT XML 파일을 파싱, 결과 반환."""

    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".xml", ".rdf")):
        extension = pathlib.Path(file.filename).suffix.lower()
        raise MetadataEntryNotSupportedTypeError(type=extension)

    content = await file.read()
    parsed_data = converter.convert_to_table(content)

    return APIResponseModel(result=parsed_data, description="DCAT XML 파일 파싱 완료")


@router.get("/select/{metadata_id}")
async def select_metadata(
        session: SessionDep,
        service: MetadataEntryService = Depends(get_metadata_entry_service),
        metadata_id: str = Path(
            description="조회할 메타데이터 엔트리의 ID: UUID",
            title="Metadata Entry ID",
            example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd"
        ),
):
    """파싱된 raw 메타데이터를 조회."""
    result = service.select_metadata(session, metadata_id=metadata_id)

    return APIResponseModel(result=result, description="Metadata Found.")
