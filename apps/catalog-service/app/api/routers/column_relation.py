from fastapi import APIRouter, Query

from app.dependencies import SessionDep
from app.schemas.response import APIResponseModel
from app.src.column_relation.dependencies import ColumnRelationServiceDep
from app.src.column_relation.model import ColumnRelationBase

router = APIRouter(prefix="/relation", tags=["relation"])


@router.post("/")
async def create_column_relation(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    catalog_column: str = Query(description="카탈로그 컬럼명"),
    metadata_column: str = Query(description="메타데이터 컬럼명"),
    correlation: float = Query(1.0, description="상관관계 점수 (0.0-1.0)", ge=0.0, le=1.0),
):
    """카탈로그와 메타데이터 컬럼 간 관계 생성"""
    result = service.create_single_relation(
        db=session,
        relation=ColumnRelationBase(catalog_column=catalog_column, metadata_column=metadata_column, correlation=correlation),
    )

    return APIResponseModel(result=result, description="Created Relation.")


@router.get("/catalog-column")
async def get_relations_by_catalog_column(
    session: SessionDep, service: ColumnRelationServiceDep, catalog_column: str = Query(description="조회할 카탈로그 컬럼명")
):
    """카탈로그 컬럼명으로 연관된 모든 관계 조회"""

    result = service.get_relations_by_catalog_column(db=session, catalog_column=catalog_column)

    return APIResponseModel(result=result, description="Found related Relations by catalog_column.")


@router.get("/metadata-column")
async def get_relations_by_metadata_column(
    session: SessionDep,
    service: ColumnRelationServiceDep,
    metadata_column: str = Query(description="조회할 메타데이터 컬럼명"),
):
    """메타데이터 컬럼명으로 연관된 모든 관계 조회"""
    result = service.get_relations_by_metadata_column(db=session, metadata_column=metadata_column)

    return APIResponseModel(result=result, description="Found related Relations by metadata_column.")
