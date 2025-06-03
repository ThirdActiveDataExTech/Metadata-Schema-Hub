"""
PUT, POST, GET 에 대한 다양한 API 예시를 작성해놨으니 참고해서 개발을 진행한다.
되도록이면 Swagger에서 API를 쉽게 파악하기 위해 API 및 Body, Path, Query에 대한 설명을 작성한다.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.schemas.response import APIResponseModel
from app.src.metadata_entry.json_converter import JsonConverter
from app.src.metadata_entry.xml_converter import LxmlConverter

router = APIRouter(prefix="/metadata", tags=["metadata"])


def get_json_converter():
    return JsonConverter()


def get_rdf_converter():
    return LxmlConverter()


@router.post("/import/schema-org")
async def import_schema_org(
        converter: JsonConverter = Depends(get_json_converter),
        file: UploadFile = File(description="Schema.org JSON 형식의 메타데이터 파일", media_type="application/json"),
):
    """Schema.org JSON 파일을 업로드 후 카탈로그에 저장."""
    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".json", ".jsonld")):
        raise HTTPException(status_code=400, detail="JSON 파일만 업로드 가능")

    content = await file.read()
    parsed_data = converter.convert_to_table(content)

    return APIResponseModel(result=parsed_data, description="Schema.org JSON import 완료")


@router.post("/import/dcat")
async def import_dcat(
        converter: LxmlConverter = Depends(get_rdf_converter),
        file: UploadFile = File(description="DCAT XML/RDF 형식의 메타데이터 파일", media_type="application/xml"),
):
    """DCAT XML 파일을 업로드하여 파싱된 메타데이터를 반환"""

    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".xml", ".rdf")):
        raise HTTPException(status_code=400, detail="XML 또는 RDF 파일만 업로드 가능")

    content = await file.read()
    parsed_data = converter.convert_to_table(content)

    return APIResponseModel(result=parsed_data, description="DCAT XML 파일 파싱 완료")
