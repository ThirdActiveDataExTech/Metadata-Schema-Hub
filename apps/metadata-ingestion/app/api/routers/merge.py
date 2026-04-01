"""Merge API endpoints."""

from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.catalog_merge.dependencies import CatalogMergeServiceDep
from app.src.workflow.dependencies import IngestionWorkflowServiceDep

router = APIRouter(
    prefix="/merge",
    tags=["merge"],
    route_class=ExceptionHandlingRoute,
)


# --- Request DTOs ---


class MergeApproveRequest(BaseModel):
    """Merge approve request body."""

    decided_by: str
    target_entry_id: int | None = None


class MergeRejectRequest(BaseModel):
    """Merge reject request body."""

    decided_by: str


# --- Endpoints ---


@router.get(
    "/entries",
    summary="머지 목록 조회",
    response_model=APIResponseModel,
)
async def list_merges(
    session: SessionDep,
    merge_service: CatalogMergeServiceDep,
    draft_id: Annotated[
        Optional[int],
        Query(title="드래프트 ID", description="특정 드래프트 ID로 필터링"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> APIResponseModel:
    """머지 목록을 조회합니다."""
    if draft_id:
        merge = merge_service.get_merge_by_draft(session, draft_id)
        merges = [merge] if merge else []
    else:
        merges = merge_service.get_all_merges(session, limit, offset)

    return APIResponseModel(
        result={
            "merges": [m.model_dump() for m in merges],
            "count": len(merges),
            "limit": limit,
            "offset": offset,
        },
        description=f"총 {len(merges)}건 조회",
    )


@router.get(
    "/entries/{merge_id}",
    summary="머지 상세 조회",
    response_model=APIResponseModel,
    responses={404: {"description": "해당 ID의 머지가 존재하지 않음"}},
)
async def get_merge(
    session: SessionDep,
    merge_service: CatalogMergeServiceDep,
    merge_id: int = Path(title="머지 ID", ge=1),
) -> APIResponseModel:
    """특정 머지의 상세 정보를 조회합니다."""
    merge = merge_service.get_merge(session, merge_id)
    if not merge:
        raise HTTPException(status_code=404, detail=f"CatalogMerge {merge_id} not found")

    return APIResponseModel(
        result=merge.model_dump(),
        description=f"머지 {merge_id} 조회 완료",
    )


@router.get(
    "/entries/by-draft/{draft_id}",
    summary="드래프트별 머지 조회",
    response_model=APIResponseModel,
    responses={404: {"description": "해당 드래프트의 머지가 존재하지 않음"}},
)
async def get_merge_by_draft(
    session: SessionDep,
    merge_service: CatalogMergeServiceDep,
    draft_id: int = Path(title="드래프트 ID", ge=1),
) -> APIResponseModel:
    """드래프트 ID로 머지를 조회합니다."""
    merge = merge_service.get_merge_by_draft(session, draft_id)
    if not merge:
        raise HTTPException(status_code=404, detail=f"CatalogMerge for draft {draft_id} not found")

    return APIResponseModel(
        result=merge.model_dump(),
        description=f"드래프트 {draft_id}의 머지 조회 완료",
    )


@router.post(
    "/entries/{merge_id}/approve",
    summary="머지 승인",
    response_model=APIResponseModel,
    responses={
        400: {"description": "승인 조건 미충족 (PENDING 상태가 아님)"},
        404: {"description": "해당 ID의 머지가 존재하지 않음"},
    },
)
async def approve_merge(
    session: SessionDep,
    workflow_service: IngestionWorkflowServiceDep,
    request: MergeApproveRequest,
    merge_id: int = Path(title="머지 ID", ge=1),
) -> APIResponseModel:
    """머지를 승인하고 CatalogEntry를 생성/갱신합니다. (승인 = 승인 + 발행)"""
    merge, catalog_entry = workflow_service.execute_merge_approve(
        session, merge_id, request.decided_by, request.target_entry_id
    )

    return APIResponseModel(
        result={
            **merge.model_dump(),
            "catalog_entry_id": catalog_entry.id,
            "catalog_entry_identifier": catalog_entry.identifier,
        },
        description=f"머지 {merge_id} 승인 완료, 카탈로그 엔트리 {catalog_entry.id} 생성",
    )


@router.post(
    "/entries/{merge_id}/reject",
    summary="머지 거부",
    response_model=APIResponseModel,
    responses={
        400: {"description": "거부 조건 미충족 (PENDING 상태가 아님)"},
        404: {"description": "해당 ID의 머지가 존재하지 않음"},
    },
)
async def reject_merge(
    session: SessionDep,
    merge_service: CatalogMergeServiceDep,
    request: MergeRejectRequest,
    merge_id: int = Path(title="머지 ID", ge=1),
) -> APIResponseModel:
    """머지를 거부합니다."""
    merge = merge_service.reject(session, merge_id, request.decided_by)

    return APIResponseModel(
        result=merge.model_dump(),
        description=f"머지 {merge_id} 거부 완료",
    )
