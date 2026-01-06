import io
import json
from datetime import date
from typing import Annotated, Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Path, Query
from starlette.responses import StreamingResponse

from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.catalog_entry.dependencies import CatalogEntryServiceDep
from app.src.catalog_entry.model import CatalogEntrySummary
from app.src.catalog_entry.schemas import CatalogEntryResponse
from app.src.workflow.dependencies import CatalogEntryTransformServiceDep

router = APIRouter(prefix="/catalog", tags=["catalog"], route_class=ExceptionHandlingRoute)


@router.get(
    "/entries/{catalog_entry_id}",
    summary="카탈로그 엔트리 조회",
    response_model=APIResponseModel[CatalogEntryResponse],
)
async def get_catalog_entry(
    session: SessionDep,
    service: CatalogEntryServiceDep,
    catalog_entry_id: int = Path(
        title="카탈로그 엔트리 ID",
        description="조회할 카탈로그 엔트리의 고유 식별 번호",
        example=31,
        ge=1,
    ),
):
    """특정 카탈로그 엔트리의 상세 정보를 조회합니다.

    Args:
        catalog_entry_id: 조회할 카탈로그 엔트리의 데이터베이스 ID

    Returns:
        DCAT 표준 기반의 카탈로그 엔트리 정보

    Raises:
        404: 해당 ID의 카탈로그 엔트리가 존재하지 않음
    """
    catalog_entry = service.get_catalog_entry(db=session, catalog_entry_id=catalog_entry_id)
    return APIResponseModel(result=catalog_entry, description="Entry Found.")


@router.get(
    "/entries/raw-metadata/{catalog_entry_id}",
    summary="원본 메타데이터 조회",
    response_model=APIResponseModel[str],
)
async def get_raw_metadata(
    session: SessionDep,
    service: CatalogEntryServiceDep,
    catalog_entry_id: int = Path(
        title="카탈로그 엔트리 ID",
        description="조회할 카탈로그 엔트리의 고유 식별 번호",
        example=31,
        ge=1,
    ),
    output_format: Literal["json", "xml"] = Query(
        default="json",
        title="출력 형식",
        description="원본 메타데이터 출력 형식 (json: JSON-LD, xml: RDF/XML)",
        examples=["json", "xml"],
    ),
):
    """카탈로그 엔트리의 원본 메타데이터를 지정된 형식으로 조회합니다.

    수집 시점의 원본 메타데이터를 변환 없이 그대로 반환합니다.
    JSON 또는 XML 형식으로 출력할 수 있습니다.

    Args:
        catalog_entry_id: 조회할 카탈로그 엔트리의 데이터베이스 ID
        output_format: 출력 형식 (json 또는 xml)

    Returns:
        원본 메타데이터 (지정된 형식으로 변환됨)

    Raises:
        404: 해당 ID의 카탈로그 엔트리가 존재하지 않음
    """
    catalog_entry = service.get_raw_metadata(db=session, catalog_entry_id=catalog_entry_id, data_format=output_format)
    return APIResponseModel(result=catalog_entry, description="Raw Metadata Found.")


@router.get(
    "/entries/{catalog_entry_id}/rdf",
    summary="RDF 표현 조회",
    response_model=APIResponseModel[Dict[str, Any]],
)
async def get_rdf_representation(
    session: SessionDep,
    service: CatalogEntryServiceDep,
    catalog_entry_id: int = Path(
        title="카탈로그 엔트리 ID",
        description="조회할 카탈로그 엔트리의 고유 식별 번호",
        example=31,
        ge=1,
    ),
):
    """카탈로그 엔트리의 RDF 표현을 JSON-LD 형식으로 반환합니다.

    DCAT(Data Catalog Vocabulary) 표준에 따라 정규화된 메타데이터를 제공합니다.
    반환된 JSON-LD는 Semantic Web 환경에서 직접 사용 가능하며,
    외부 시스템과의 메타데이터 교환 시 표준 포맷으로 활용됩니다.

    Args:
        catalog_entry_id: 조회할 카탈로그 엔트리의 데이터베이스 ID

    Returns:
        DCAT 기반 RDF 메타데이터 (JSON-LD 형식)

    Raises:
        404: 해당 ID의 카탈로그 엔트리가 존재하지 않음
    """
    catalog_entry = service.get_catalog_entry(db=session, catalog_entry_id=catalog_entry_id)
    rdf_representation = catalog_entry.get_rdf_dict()
    return APIResponseModel(result=rdf_representation, description="RDF Metadata Found.")


@router.get(
    "/entries/{catalog_entry_id}/rdf/download",
    summary="RDF 파일 다운로드",
    responses={
        200: {
            "description": "JSON-LD 파일 다운로드 성공",
            "content": {"application/ld+json": {"example": {}}},
        }
    },
)
async def download_rdf_representation(
    session: SessionDep,
    service: CatalogEntryServiceDep,
    catalog_entry_id: int = Path(
        title="카탈로그 엔트리 ID",
        description="다운로드할 카탈로그 엔트리의 고유 식별 번호",
        example=31,
        ge=1,
    ),
):
    """카탈로그 엔트리의 RDF 표현을 JSON-LD 파일로 다운로드합니다.

    DCAT(Data Catalog Vocabulary) 표준에 따라 정규화된 메타데이터를 JSON-LD 파일로 제공합니다.
    다운로드된 파일은 Semantic Web 환경에서 직접 사용 가능하며,
    외부 시스템과의 메타데이터 교환 시 표준 포맷으로 활용됩니다.

    Args:
        catalog_entry_id: 다운로드할 카탈로그 엔트리의 데이터베이스 ID

    Returns:
        StreamingResponse: DCAT 기반 RDF 메타데이터 JSON-LD 파일

    Raises:
        404: 해당 ID의 카탈로그 엔트리가 존재하지 않음
    """
    catalog_entry = service.get_catalog_entry(db=session, catalog_entry_id=catalog_entry_id)
    rdf_dict = catalog_entry.get_rdf_dict()

    # JSON-LD를 보기 좋게 포맷팅
    json_content = json.dumps(rdf_dict, ensure_ascii=False, indent=2)

    # 파일명 생성 (카탈로그 엔트리 ID 포함)
    filename = f"catalog_entry_{catalog_entry_id}_rdf.json"

    return StreamingResponse(
        io.BytesIO(json_content.encode("utf-8")),
        media_type="application/ld+json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/entries",
    summary="카탈로그 엔트리 검색 및 목록 조회",
    response_model=APIResponseModel[List[CatalogEntrySummary]],
)
async def search_catalog_entries(
    session: SessionDep,
    service: CatalogEntryServiceDep,
    query: Annotated[
        Optional[str],
        Query(
            title="검색어",
            description="제목, 설명 텍스트 검색 (LIKE 패턴)",
            openapi_examples={
                "simple": {"summary": "간단한 검색", "value": "데이터"},
                "statistics": {"summary": "통계 데이터 검색", "value": "통계"},
            },
        ),
    ] = None,
    keyword: Annotated[
        Optional[List[str]],
        Query(
            title="키워드 필터",
            description="키워드 배열 필터 (여러 키워드 중 하나라도 일치하면 검색됨)",
            openapi_examples={
                "single": {"summary": "단일 키워드", "value": ["에너지"]},
                "multiple": {"summary": "복수 키워드", "value": ["재난", "화물"]},
            },
        ),
    ] = None,
    theme: Annotated[
        Optional[List[str]],
        Query(
            title="주제 분류 필터",
            description="주제 분류 배열 필터 (여러 주제 중 하나라도 일치하면 검색됨)",
            openapi_examples={
                "health": {"summary": "단일 주제", "value": ["환경"]},
                "transport": {"summary": "여러 주제", "value": ["교통및물류", "산업·통상·중소기업"]},
            },
        ),
    ] = None,
    date_field: Annotated[
        Optional[Literal["issued", "modified", "ingested_at", "updated_at"]],
        Query(
            title="날짜 필터링 필드",
            description="날짜 범위 필터링을 적용할 필드 선택",
            openapi_examples={
                "issued": {"summary": "발행일 필터", "value": "issued"},
                "modified": {"summary": "수정일 필터", "value": "modified"},
                "ingested_at": {"summary": "수집일시 필터", "value": "ingested_at"},
                "updated_at": {"summary": "갱신일시 필터", "value": "updated_at"},
            },
        ),
    ] = None,
    date_from: Annotated[
        Optional[date],
        Query(
            title="날짜 범위 시작",
            description="날짜 범위 필터의 시작일 (date_field와 함께 사용, YYYY-MM-DD 형식)",
            openapi_examples={
                "year_start": {"summary": "2024년 시작", "value": "2024-01-01"},
                "month_start": {"summary": "12월 시작", "value": "2024-12-01"},
            },
        ),
    ] = None,
    date_to: Annotated[
        Optional[date],
        Query(
            title="날짜 범위 종료",
            description="날짜 범위 필터의 종료일 (date_field와 함께 사용, YYYY-MM-DD 형식)",
            openapi_examples={
                "year_end": {"summary": "2026년 종료", "value": "2026-12-31"},
                "month_end": {"summary": "6월 종료", "value": "2026-06-30"},
            },
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            title="결과 제한",
            description="검색 결과 최대 개수",
            openapi_examples={
                "small": {"summary": "소량 조회", "value": 10},
                "large": {"summary": "대량 조회", "value": 100},
            },
        ),
    ] = 10,
    offset: Annotated[
        int,
        Query(
            ge=0,
            title="결과 시작 위치",
            description="검색 결과 시작 위치 (0부터 시작, 페이징에 사용)",
            openapi_examples={
                "first_page": {"summary": "첫 페이지", "value": 0},
                "second_page": {"summary": "두 번째 페이지 (limit=20)", "value": 20},
                "third_page": {"summary": "세 번째 페이지 (limit=20)", "value": 40},
            },
        ),
    ] = 0,
    sort_field: Annotated[
        Optional[str],
        Query(
            title="정렬 필드",
            description="정렬할 필드 선택 (id, title, issued, modified, ingested_at, updated_at, publisher)",
            openapi_examples={
                "issued": {"summary": "발행일 정렬", "value": "issued"},
                "updated": {"summary": "갱신일 정렬", "value": "updated_at"},
                "title": {"summary": "제목 정렬", "value": "title"},
            },
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Literal["asc", "desc"]],
        Query(
            title="정렬 방향",
            description="정렬 방향 (asc: 오름차순, desc: 내림차순)",
            openapi_examples={
                "desc": {"summary": "내림차순", "value": "desc"},
                "asc": {"summary": "오름차순", "value": "asc"},
            },
        ),
    ] = None,
):
    """카탈로그 엔트리를 검색하거나 전체 목록을 조회합니다.

    검색 조건이 제공되면 해당 조건으로 검색하고, 조건이 없으면 전체 목록을 반환합니다.
    텍스트 검색, 키워드/주제 필터링, 날짜 범위 검색, 페이징, 정렬 기능을 지원합니다.

    검색 조건 결합 방식:
    - 서로 다른 조건(query, keyword, theme, date_field 등)은 AND로 결합됩니다.
    - 동일 조건 내 배열 값(keyword 배열, theme 배열)은 OR로 검색됩니다.
    """
    result = service.search_catalog(
        db=session,
        query=query,
        keyword=keyword,
        theme=theme,
        date_field=date_field,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
        sort_field=sort_field,
        sort_order=sort_order,
    )

    has_search_params = bool(query or keyword or theme or date_field)
    description = f"{'검색' if has_search_params else '목록 조회'} 완료. 총 {len(result)}건 조회"

    return APIResponseModel(result=result, description=description)


@router.get(
    "/export/csv",
    summary="CSV 파일로 내보내기",
    responses={
        200: {
            "description": "CSV 파일 다운로드 성공",
            "content": {"text/csv": {}},
        }
    },
)
async def export_catalog_entries_csv(
    session: SessionDep,
    service: CatalogEntryServiceDep,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            title="내보낼 개수",
            description="내보낼 카탈로그 엔트리 개수 제한",
            openapi_examples={
                "standard": {"summary": "표준 내보내기", "value": 100},
                "medium": {"summary": "중량 내보내기", "value": 500},
                "maximum": {"summary": "최대 내보내기", "value": 1000},
            },
        ),
    ] = 100,
):
    """카탈로그 엔트리를 CSV 파일로 내보냅니다.

    지정된 개수만큼의 카탈로그 엔트리를 CSV 형식으로 변환하여
    다운로드 가능한 파일로 제공합니다.

    Args:
        limit: 내보낼 카탈로그 엔트리 개수 제한

    Returns:
        StreamingResponse: CSV 형식의 카탈로그 엔트리 데이터
    """
    csv_stream = service.export_to_csv_stream(session, limit)
    return StreamingResponse(
        io.StringIO(csv_stream.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=catalog_entries.csv"},
    )


@router.put(
    "/match/relations/{catalog_entry_id}",
    summary="컬럼 관계 기반 카탈로그 갱신",
    response_model=APIResponseModel[CatalogEntryResponse],
)
async def match_relations(
    session: SessionDep,
    catalog_transform_service: CatalogEntryTransformServiceDep,
    catalog_entry_id: int = Path(
        title="카탈로그 엔트리 ID",
        description="갱신할 카탈로그 엔트리의 고유 식별 번호",
        example=31,
        ge=1,
    ),
):
    """컬럼 관계 정보를 기반으로 카탈로그 엔트리를 갱신합니다.

    메타데이터 엔트리와 컬럼 관계(column_relation) 테이블의 매핑 정보를 이용하여
    카탈로그 엔트리의 DCAT 표준 필드들을 자동으로 갱신합니다.

    Args:
        catalog_entry_id: 갱신할 카탈로그 엔트리의 데이터베이스 ID

    Returns:
        갱신된 카탈로그 엔트리 정보

    Raises:
        404: 해당 ID의 카탈로그 엔트리가 존재하지 않음

    Note:
        이 API는 메타데이터 수집 후 자동으로 호출되며, 수동으로 재매핑이 필요한 경우에도 사용할 수 있습니다.
    """
    updated_catalog_entry = catalog_transform_service.update_catalog_entry_from_metadata_and_relation(
        db=session, catalog_entry_id=catalog_entry_id
    )
    return APIResponseModel(result=updated_catalog_entry, description="카탈로그 엔트리 갱신됨")
