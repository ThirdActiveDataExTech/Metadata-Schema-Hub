from fastapi import APIRouter, Depends

from app.dependencies import SessionDep
from app.schemas.column_relation import ColumnRelationBase
from app.schemas.response import APIResponseModel
from app.src.column_relation.repository import ColumnRelationRepository
from app.src.column_relation.service import ColumnRelationService

router = APIRouter(prefix="/relation", tags=["relation"])


def get_column_relation_service(repository=Depends(ColumnRelationRepository)):
    """Repository dependency injection."""
    return ColumnRelationService(repository)


@router.post("/create")
async def create_single_relation(
        session: SessionDep,
        service: ColumnRelationService = Depends(get_column_relation_service),
        catalog_column: str = "",
        metadata_column: str = "",
        correlation: float = 1.0,

):
    result = service.create_single_relation(db=session, relation=ColumnRelationBase(
        catalog_column=catalog_column,
        metadata_column=metadata_column,
        correlation=correlation
    ))

    return APIResponseModel(result=result, description="Created Relation.")


@router.get("/catalog-column")
async def get_relation_by_catalog_column(
        session: SessionDep,
        service: ColumnRelationService = Depends(get_column_relation_service),
        catalog_column: str = ""
):
    result = service.get_relations_by_catalog_column(db=session, catalog_column=catalog_column)

    return APIResponseModel(result=result, description="Found related Relations by catalog_column.")


@router.get("/metadata-column")
async def get_relation_by_metadata_column(
        session: SessionDep,
        service: ColumnRelationService = Depends(get_column_relation_service),
        metadata_column: str = ""
):
    result = service.get_relations_by_metadata_column(db=session, metadata_column=metadata_column)

    return APIResponseModel(result=result, description="Found related Relations by metadata_column.")
