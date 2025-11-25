from fastapi import APIRouter, Query

from app.dependencies import SessionDep
from app.schemas.response import APIResponseModel
from app.src.column_relation.dependencies import ColumnRelationServiceDep
from app.src.column_relation.model import ColumnRelationBase

router = APIRouter(prefix="/relation", tags=["relation"])


@router.post(
    "/",
    summary="컬럼 관계 생성",
    response_model=APIResponseModel,
)
async def create_column_relation(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    catalog_column: str = Query(
        description="카탈로그 테이블의 컬럼명",
        examples=["title", "description", "publisher"],
    ),
    metadata_column: str = Query(
        description="메타데이터 테이블의 스키마명",
        examples=["dct:title", "schema:name", "dcat:keyword"],
    ),
    correlation: float = Query(
        1.0,
        description="컬럼 간 연관성 점수 (0.0-1.0)",
        ge=0.0,
        le=1.0,
        example=0.95,
    ),
):
    """카탈로그 컬럼과 메타데이터 컬럼 간의 매핑 관계를 생성합니다.

    두 컬럼 간의 의미적 연관성과 신뢰도를 점수로 기록하여,
    메타데이터 수집 시 자동 매핑에 활용됩니다.

    Args:
        catalog_column: 카탈로그 테이블의 대상 컬럼명
        metadata_column: 메타데이터 테이블의 스키마명
        correlation: 연관성 점수 (0.0=무관, 1.0=완전일치)

    Returns:
        생성된 컬럼 관계 정보

    Examples:
        - catalog_column="title", metadata_column="dct:title", correlation=1.0
        - catalog_column="description", metadata_column="schema:description", correlation=0.95
    """
    result = service.create_single_relation(
        db=session,
        relation=ColumnRelationBase(catalog_column=catalog_column, metadata_column=metadata_column, correlation=correlation),
    )

    return APIResponseModel(result=result, description="Created Relation.")


@router.get(
    "/catalog-column",
    summary="카탈로그 컬럼 기반 관계 조회",
    response_model=APIResponseModel,
)
async def get_relations_by_catalog_column(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    catalog_column: str = Query(
        description="조회할 카탈로그 테이블의 컬럼명",
        examples=["title", "description", "keyword"],
    ),
):
    """특정 카탈로그 컬럼과 매핑된 모든 메타데이터 컬럼을 조회합니다.

    주어진 카탈로그 컬럼에 연관된 모든 메타데이터 스키마와
    각각의 연관성 점수를 반환합니다.

    Args:
        catalog_column: 조회할 카탈로그 테이블의 컬럼명

    Returns:
        해당 카탈로그 컬럼과 연관된 관계 목록

    Note:
        결과는 연관성 점수 기준으로 내림차순 정렬됩니다.
    """

    result = service.get_relations_by_catalog_column(db=session, catalog_column=catalog_column)

    return APIResponseModel(result=result, description="Found related Relations by catalog_column.")


@router.get(
    "/metadata-column",
    summary="메타데이터 컬럼 기반 관계 조회",
    response_model=APIResponseModel,
)
async def get_relations_by_metadata_column(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    metadata_column: str = Query(
        description="조회할 메타데이터 테이블의 스키마명",
        examples=["dct:title", "schema:description", "dcat:keyword"],
    ),
):
    """특정 메타데이터 컬럼과 매핑된 모든 카탈로그 컬럼을 조회합니다.

    주어진 메타데이터 스키마에 연관된 모든 카탈로그 컬럼과
    각각의 연관성 점수를 반환합니다.

    Args:
        metadata_column: 조회할 메타데이터 테이블의 스키마명

    Returns:
        해당 메타데이터 컬럼과 연관된 관계 목록

    Note:
        결과는 연관성 점수 기준으로 내림차순 정렬됩니다.
    """
    result = service.get_relations_by_metadata_column(db=session, metadata_column=metadata_column)

    return APIResponseModel(result=result, description="Found related Relations by metadata_column.")
