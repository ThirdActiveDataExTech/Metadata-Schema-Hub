import io
import json
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Path, Query
from starlette.responses import StreamingResponse

from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.catalog_entry.service import CatalogEntryService
from app.src.column_relation.repository import ColumnRelationRepository
from app.src.column_relation.service import ColumnRelationService
from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.service import MetadataEntryService
from app.src.workflow.transform_service import CatalogEntryTransformService

router = APIRouter(prefix="/catalog", tags=["catalog"], route_class=ExceptionHandlingRoute)


def get_catalog_entry_service(repository=Depends(CatalogEntryRepository)) -> CatalogEntryService:
    """Repository dependency injection."""
    return CatalogEntryService(repository)


def get_column_relation_service(repository=Depends(ColumnRelationRepository)) -> ColumnRelationService:
    """Repository dependency injection."""
    return ColumnRelationService(repository)


def get_metadata_entry_service(repository=Depends(MetadataEntryRepository)) -> MetadataEntryService:
    """Repository dependency injection."""
    return MetadataEntryService(repository)


def get_catalog_entry_transform_service(
    catalog_entry_service=Depends(get_catalog_entry_service),
    column_relation_service=Depends(get_column_relation_service),
    metadata_entry_service=Depends(get_metadata_entry_service),
) -> CatalogEntryTransformService:
    """Repository dependency injection."""
    return CatalogEntryTransformService(
        catalog_entry_service=catalog_entry_service,
        column_relation_service=column_relation_service,
        metadata_entry_service=metadata_entry_service,
    )


@router.get("/entries/{catalog_entry_id}")
async def get_catalog_entry(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    catalog_entry_id: int = Path(description="조회할 카탈로그 엔트리 ID", example=31),
):
    """특정 카탈로그 엔트리 조회"""
    catalog_entry = service.get_catalog_entry(db=session, catalog_entry_id=catalog_entry_id)
    return APIResponseModel(result=catalog_entry, description="Entry Found.")


@router.get("/entries/raw-metadata/{catalog_entry_id}")
async def get_raw_metadata(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    catalog_entry_id: int = Path(description="조회할 카탈로그 엔트리 ID", example=31),
    output_format: Literal["json", "xml"] = Query(default="json", description="출력 형식 선택", example="json"),
):
    """특정 카탈로그 엔트리의 원본 메타데이터 조회"""
    catalog_entry = service.get_raw_metadata(db=session, catalog_entry_id=catalog_entry_id, data_format=output_format)
    return APIResponseModel(result=catalog_entry, description="Raw Metadata Found.")


@router.get("/entries/{catalog_entry_id}/rdf")
async def get_rdf_representation(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    catalog_entry_id: int = Path(description="조회할 카탈로그 엔트리 ID", example=31),
):
    """카탈로그 엔트리의 RDF 표현을 JSON-LD 형식으로 반환

    DCAT(Data Catalog Vocabulary) 표준에 따라 정규화된 메타데이터를 제공합니다.
    반환된 JSON-LD는 Semantic Web 환경에서 직접 사용 가능하며,
    외부 시스템과의 메타데이터 교환 시 표준 포맷으로 활용됩니다.

    Args:
        catalog_entry_id: 조회할 카탈로그 엔트리의 고유 식별자

    Returns:
        DCAT 기반 RDF 메타데이터 (JSON-LD 형식)
    """
    catalog_entry = service.get_catalog_entry(db=session, catalog_entry_id=catalog_entry_id).get_rdf_dict()
    return APIResponseModel(result=catalog_entry, description="RDF Metadata Found.")


@router.get("/entries/{catalog_entry_id}/rdf/download")
async def download_rdf_representation(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    catalog_entry_id: int = Path(description="다운로드할 카탈로그 엔트리 ID", example=31),
):
    """카탈로그 엔트리의 RDF 표현을 JSON-LD 파일로 다운로드

    DCAT(Data Catalog Vocabulary) 표준에 따라 정규화된 메타데이터를 JSON-LD 파일로 제공합니다.
    다운로드된 파일은 Semantic Web 환경에서 직접 사용 가능하며,
    외부 시스템과의 메타데이터 교환 시 표준 포맷으로 활용됩니다.

    Args:
        catalog_entry_id: 다운로드할 카탈로그 엔트리의 고유 식별자

    Returns:
        DCAT 기반 RDF 메타데이터 JSON-LD 파일
    """
    catalog_entry = service.get_catalog_entry(db=session, catalog_entry_id=catalog_entry_id)
    rdf_dict = catalog_entry.get_rdf_dict()

    # JSON-LD를 보기 좋게 포맷팅
    json_content = json.dumps(rdf_dict, ensure_ascii=False, indent=2)
    json_stream = io.StringIO(json_content)

    # 파일명 생성 (카탈로그 엔트리 ID 포함)
    filename = f"catalog_entry_{catalog_entry_id}_rdf.jsonld"

    return StreamingResponse(
        json_stream,
        media_type="application/ld+json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/entries")
async def search_catalog_entries(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    query: Optional[str] = Query(None, description="제목, 설명 텍스트 검색 (LIKE 패턴)"),
    keyword: Optional[str] = Query(None, description="키워드 정확 일치 필터"),
    limit: int = Query(10, description="검색 결과 제한 개수", ge=1, le=100),  # TODO: test 되지 않은 limit
):
    """카탈로그 엔트리 검색 (쿼리 또는 키워드 기반)"""

    # 검색 조건 존재 여부 확인
    has_search_params = bool(query or keyword)

    if has_search_params:
        # 검색 수행
        result = service.search_catalog(db=session, query=query, keyword=keyword)
        description = f"검색 완료. 총 {len(result)}건 조회"
    else:
        # 전체 목록 조회
        result = service.list_catalog(db=session, limit=limit)
        # limit 적용 (서비스에서 지원하지 않는 경우 슬라이싱)
        if len(result) > limit:
            result = result[:limit]
        description = f"목록 조회 완료. 총 {len(result)}건 조회"

    return APIResponseModel(result=result, description=description)


@router.get("/export/csv")
async def export_catalog_entries_csv(
    session: SessionDep,
    service: CatalogEntryService = Depends(get_catalog_entry_service),
    limit: int = Query(100, description="내보낼 엔트리 개수 제한"),  # TODO: test 되지 않은 limit
):
    """카탈로그 엔트리를 CSV 파일로 내보내기"""
    csv_stream = service.export_to_csv_stream(session, limit)
    return StreamingResponse(
        io.StringIO(csv_stream.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=catalog_entries.csv"},
    )


@router.put("/match/relations/{catalog_entry_id}")
async def match_relations(
    session: SessionDep,
    catalog_transform_service: CatalogEntryTransformService = Depends(get_catalog_entry_transform_service),
    catalog_entry_id: int = Path(description="갱신할 카탈로그 엔트리 ID", example=31),
):
    updated_catalog_entry = catalog_transform_service.update_catalog_entry_from_metadata_and_relation(
        db=session, catalog_entry_id=catalog_entry_id
    )
    return APIResponseModel(result=updated_catalog_entry, description="카탈로그 엔트리 갱신됨")
