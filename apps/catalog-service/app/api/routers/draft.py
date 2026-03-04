"""Draft API endpoints (read-only)."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.catalog_entry_draft.dependencies import CatalogEntryDraftServiceDep

router = APIRouter(
    prefix="/draft",
    tags=["draft"],
    route_class=ExceptionHandlingRoute,
)


@router.get(
    "/entries",
    summary="List catalog entry drafts",
    response_model=APIResponseModel,
)
async def list_drafts(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    snapshot_id: Optional[str] = Query(None, description="Filter by snapshot_id"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> APIResponseModel:
    """List catalog entry drafts with optional filters."""
    if snapshot_id:
        drafts = draft_service.get_drafts_by_snapshot(session, snapshot_id, limit, offset)
    else:
        drafts = draft_service.get_all_drafts(session, limit, offset)

    return APIResponseModel(
        result={
            "drafts": [d.to_summary_dict() for d in drafts],
            "count": len(drafts),
            "limit": limit,
            "offset": offset,
        },
        description=f"Found {len(drafts)} drafts",
    )


@router.get(
    "/entries/{draft_id}",
    summary="Get draft details",
    response_model=APIResponseModel,
)
async def get_draft(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    draft_id: int,
) -> APIResponseModel:
    """Get details of a specific draft including mapping evidence."""
    draft = draft_service.get_draft(session, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    return APIResponseModel(
        result=draft.to_api_dict(),
        description=f"Draft {draft_id}",
    )


@router.get(
    "/entries/{draft_id}/evidence",
    summary="Get mapping evidence only",
    response_model=APIResponseModel,
)
async def get_draft_evidence(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    draft_id: int,
) -> APIResponseModel:
    """Get only the mapping evidence for a draft."""
    draft = draft_service.get_draft(session, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    return APIResponseModel(
        result={
            "draft_id": draft_id,
            "mapping_evidence": draft.mapping_evidence,
        },
        description=f"Mapping evidence for draft {draft_id}",
    )
