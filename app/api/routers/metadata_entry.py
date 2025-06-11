import pathlib
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, Path, Query

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

@router.get("/entries")
async def search_metadata_entries(
    session: SessionDep,
    service: MetadataEntryService = Depends(get_metadata_entry_service),
    query: Optional[str] = Query(None, description="값, 스키마 텍스트 검색 (LIKE 패턴)"),
    schema: Optional[str] = Query(None, description="메타데이터 스키마 정확 일치 필터"),
    metadata_id: Optional[str] = Query(None, description="메타데이터 ID 정확 일치 필터"),
    limit: int = Query(10, description="검색 결과 제한 개수", ge=1, le=100)  # TODO: test 되지 않은 limit
):
    """메타데이터 엔트리 검색 (쿼리, 스키마, 메타데이터 ID 기반)"""

    # 검색 조건 존재 여부 확인
    has_search_params = bool(query or schema or metadata_id)

    if has_search_params:
        # 검색 수행
        result = service.search_metadata(
            db=session,
            query=query,
            schema=schema,
            metadata_id=metadata_id
        )
        description = f"검색 완료. 총 {len(result)}건 조회"
    else:
        # 전체 목록 조회
        result = service.list_metadata(db=session, limit=limit)
        # limit 적용
        if len(result) > limit:
            result = result[:limit]
        description = f"목록 조회 완료. 총 {len(result)}건 조회"

    return APIResponseModel(
        result=result,
        description=description
    )

@router.post("/convert/schema-org")
async def convert_schema_org_metadata(
    converter: JsonConverter = Depends(get_json_converter),
    file: UploadFile = File(
        description="Schema.org JSON-LD 메타데이터 파일",
        media_type="application/json"
    ),
):
    """Schema.org JSON-LD 형식 메타데이터를 테이블 구조로 변환"""
    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".json", ".jsonld")):
        extension = pathlib.Path(file.filename).suffix.lower()
        raise MetadataEntryNotSupportedTypeError(type=extension)

    content = await file.read()
    parsed_data = converter.convert_to_table(content)

    return APIResponseModel(result=parsed_data, description="Schema.org JSON import 완료")


@router.post("/convert/dcat")
async def convert_dcat_metadata(
    converter: LxmlConverter = Depends(get_xml_converter),
    file: UploadFile = File(
        description="DCAT RDF/XML 메타데이터 파일",
        media_type="application/xml"
    ),
):
    """DCAT RDF/XML 형식 메타데이터를 테이블 구조로 변환"""

    # 파일 확장자 검증
    if not file.filename or not file.filename.endswith((".xml", ".rdf")):
        extension = pathlib.Path(file.filename).suffix.lower()
        raise MetadataEntryNotSupportedTypeError(type=extension)

    content = await file.read()
    parsed_data = converter.convert_to_table(content)

    return APIResponseModel(result=parsed_data, description="DCAT XML 파일 파싱 완료")


@router.get("/{metadata_id}")
async def get_metadata_entry(
    session: SessionDep,
    service: MetadataEntryService = Depends(get_metadata_entry_service),
    metadata_id: str = Path(
        description="메타데이터 엔트리 UUID",
        example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
        regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"  # UUID 검증 정규식
    ),
):
    """UUID로 파싱된 메타데이터 엔트리 조회"""
    result = service.select_metadata(session, metadata_id=metadata_id)

    return APIResponseModel(result=result, description="Metadata Found.")
