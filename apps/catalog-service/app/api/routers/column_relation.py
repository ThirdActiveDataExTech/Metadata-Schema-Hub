from typing import Annotated, List

from fastapi import APIRouter, Body, Query

from app.dependencies import SessionDep
from app.schemas.response import APIResponseModel
from app.src.column_relation.dependencies import ColumnRelationServiceDep
from app.src.column_relation.examples import COLUMN_RELATION_CREATE_EXAMPLES
from app.src.column_relation.model import ColumnRelationBase
from app.src.column_relation.schemas import (
    ColumnRelationCreateParams,
    ColumnRelationResponse,
)

router = APIRouter(prefix="/relation", tags=["relation"])


@router.post(
    "/",
    summary="컬럼 관계 생성",
    response_model=APIResponseModel[ColumnRelationResponse],
)
async def create_column_relation(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    params: Annotated[
        ColumnRelationCreateParams,
        Body(
            title="컬럼 관계 생성 파라미터",
            description="카탈로그 컬럼과 메타데이터 컬럼 간의 매핑 관계를 정의합니다. "
            "연관성 점수(correlation)는 0.0~1.0 사이의 값으로, 1.0에 가까울수록 의미적으로 동일함을 나타냅니다.",
            media_type="application/json",
            openapi_examples=COLUMN_RELATION_CREATE_EXAMPLES,
        ),
    ],
):
    """카탈로그 컬럼과 메타데이터 컬럼 간의 매핑 관계를 생성합니다.

    두 컬럼 간의 의미적 연관성과 신뢰도를 점수로 기록하여,
    메타데이터 수집 시 자동 매핑에 활용됩니다.

    Args:
        params: 컬럼 관계 생성 파라미터 (catalog_column, metadata_column, correlation)

    Returns:
        생성된 컬럼 관계 정보
    """
    result = service.create_single_relation(
        db=session,
        relation=ColumnRelationBase(
            catalog_column=params.catalog_column, metadata_column=params.metadata_column, correlation=params.correlation
        ),
    )

    return APIResponseModel(result=result, description="Created Relation.")


@router.get(
    "/catalog-column",
    summary="카탈로그 컬럼 기반 관계 조회",
    response_model=APIResponseModel[List[ColumnRelationResponse]],
)
async def get_relations_by_catalog_column(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    catalog_column: Annotated[
        str,
        Query(
            title="카탈로그 컬럼명",
            description="조회할 카탈로그 테이블의 컬럼명",
            openapi_examples={
                "title": {"summary": "제목 컬럼", "value": "title"},
                "description": {"summary": "설명 컬럼", "value": "description"},
                "keyword": {"summary": "키워드 컬럼", "value": "keyword"},
            },
        ),
    ],
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
    response_model=APIResponseModel[List[ColumnRelationResponse]],
)
async def get_relations_by_metadata_column(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    metadata_column: Annotated[
        str,
        Query(
            title="메타데이터 스키마명",
            description="조회할 메타데이터 테이블의 스키마명",
            openapi_examples={
                "dct_title": {"summary": "Dublin Core Title", "value": "dct:title"},
                "schema_description": {"summary": "Schema.org Description", "value": "schema:description"},
                "dcat_keyword": {"summary": "DCAT Keyword", "value": "dcat:keyword"},
            },
        ),
    ],
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
