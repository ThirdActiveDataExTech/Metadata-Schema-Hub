from typing import Annotated

from active_metadata.models import ColumnRelationBase
from fastapi import APIRouter, Body

from app.dependencies import SessionDep
from app.schemas.response import APIResponseModel
from app.src.column_relation.dependencies import ColumnRelationServiceDep
from app.src.column_relation.examples import COLUMN_RELATION_CREATE_EXAMPLES
from app.src.column_relation.schemas import (
    ColumnRelationCreateParams,
    ColumnRelationResponse,
)

router = APIRouter(prefix="/relation", tags=["relation"])


@router.post(
    "/",
    summary="컬럼 관계 생성",
    response_model=APIResponseModel[ColumnRelationResponse],
    responses={
        409: {"description": "동일한 catalog_column과 metadata_column 조합이 이미 존재함"},
        422: {"description": "요청 데이터 검증 실패 (correlation 범위 초과 등)"},
    },
)
async def create_column_relation(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    params: Annotated[
        ColumnRelationCreateParams,
        Body(
            title="컬럼 관계 생성 파라미터",
            description="카탈로그 컬럼과 메타데이터 컬럼 간의 매핑 관계를 정의합니다. "
            "연관성 점수(`correlation`)는 0.0~1.0 사이의 값으로, 1.0에 가까울수록 의미적으로 동일함을 나타냅니다.",
            media_type="application/json",
            openapi_examples=COLUMN_RELATION_CREATE_EXAMPLES,
        ),
    ],
):
    """카탈로그 컬럼과 메타데이터 컬럼 간의 매핑 관계를 생성합니다.

    두 컬럼 간의 의미적 연관성과 신뢰도를 점수로 기록하여,
    메타데이터 수집 시 자동 매핑에 활용됩니다."""
    result = service.create_single_relation(
        db=session,
        relation=ColumnRelationBase(
            catalog_column=params.catalog_column, metadata_column=params.metadata_column, correlation=params.correlation
        ),
    )

    return APIResponseModel(result=result, description="컬럼 관계 생성 완료")
