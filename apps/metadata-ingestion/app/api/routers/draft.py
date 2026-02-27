"""Draft API endpoints for metadata-ingestion."""

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
        drafts = draft_service.get_drafts_by_snapshot(session, snapshot_id)
    else:
        drafts = draft_service.get_all_drafts(session, limit, offset)

    return APIResponseModel(
        result={
            "drafts": [
                {
                    "id": d.id,
                    "snapshot_id": d.snapshot_id,
                    "mapping_version": d.mapping_version,
                    "status": d.status,
                    "title": d.title,
                    "description": d.description[:100] + "..."
                    if d.description and len(d.description) > 100
                    else d.description,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in drafts
            ],
            "count": len(drafts),
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
    evidence = draft_service.get_mapping_evidence(session, draft_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    return APIResponseModel(
        result={
            "draft_id": draft_id,
            "mapping_evidence": evidence,
        },
        description=f"Mapping evidence for draft {draft_id}",
    )


@router.post(
    "/entries/{draft_id}/publish",
    summary="Publish draft and create catalog entry",
    response_model=APIResponseModel,
)
async def publish_draft(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    draft_id: int,
) -> APIResponseModel:
    """Publish a draft and create a catalog entry."""
    try:
        catalog_entry = draft_service.publish(session, draft_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return APIResponseModel(
        result={
            "catalog_entry_id": catalog_entry.id,
            "identifier": catalog_entry.identifier,
            "title": catalog_entry.title,
            "latest_snapshot_id": catalog_entry.latest_snapshot_id,
        },
        description=f"Draft {draft_id} published, catalog entry {catalog_entry.id} created",
    )


@router.post(
    "/entries/{draft_id}/discard",
    summary="Discard a draft",
    response_model=APIResponseModel,
)
async def discard_draft(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    draft_id: int,
) -> APIResponseModel:
    """Discard a draft (mark as DISCARDED)."""
    try:
        draft = draft_service.discard(session, draft_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return APIResponseModel(
        result={
            "id": draft.id,
            "status": draft.status,
        },
        description=f"Draft {draft_id} discarded",
    )
