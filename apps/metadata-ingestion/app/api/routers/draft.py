"""Draft API endpoints for metadata-ingestion."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.catalog_entry_draft.dependencies import CatalogEntryDraftServiceDep
from app.src.catalog_entry_draft.model import DraftFieldsUpdateRequest
from app.src.metadata_entry.dependencies import MetadataEntryServiceDep

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


@router.get(
    "/entries/{draft_id}/metadata-options",
    summary="Get available metadata entries for draft editing",
    response_model=APIResponseModel,
)
async def get_metadata_options(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    metadata_service: MetadataEntryServiceDep,
    draft_id: int,
) -> APIResponseModel:
    """Get all metadata entries available for editing this draft.

    Returns the full list of metadata_entry for the draft's snapshot,
    allowing users to select any metadata value for any catalog field.
    """
    draft = draft_service.get_draft(session, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    # snapshot_id = metadata_id in metadata_entry table
    entries = metadata_service.select_metadata(session, draft.snapshot_id)

    return APIResponseModel(
        result=[{"schema": e.metadata_schema, "value": e.value} for e in entries],
        description=f"Found {len(entries)} metadata entries for draft {draft_id}",
    )


@router.patch(
    "/entries/{draft_id}",
    summary="Update draft fields by selecting metadata entries",
    response_model=APIResponseModel,
)
async def update_draft_fields(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    metadata_service: MetadataEntryServiceDep,
    draft_id: int,
    request: DraftFieldsUpdateRequest,
) -> APIResponseModel:
    """Update draft fields by selecting from available metadata entries.

    Each update specifies a catalog_field and the metadata_schema to use.
    The evidence.decided will also be updated accordingly.
    """
    # Get draft first to retrieve snapshot_id for metadata lookup
    draft = draft_service.get_draft(session, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    metadata_entries = metadata_service.select_metadata(session, draft.snapshot_id)

    updated_draft = draft_service.update_draft_fields(session, draft_id, request.updates, metadata_entries)

    return APIResponseModel(
        result=updated_draft.to_api_dict(),
        description=f"Draft {draft_id} updated ({len(request.updates)} fields)",
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
