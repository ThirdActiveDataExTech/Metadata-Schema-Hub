"""Lineage API endpoints for querying lineage events."""

from typing import Any

from fastapi import APIRouter, Path, Query

from active_metadata.models import LineageEventType
from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.lineage.dependencies import LineageEventServiceDep

router = APIRouter(prefix="/lineage", tags=["lineage"], route_class=ExceptionHandlingRoute)


@router.get(
    "/events",
    summary="List lineage events",
    response_model=APIResponseModel,
)
async def list_lineage_events(
    session: SessionDep,
    service: LineageEventServiceDep,
    job_name: str | None = Query(None, description="Job name filter"),
    event_type: LineageEventType | None = Query(None, description="Event type filter"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
) -> APIResponseModel:
    """List lineage events with optional filters."""
    events = service.list_events(
        db=session,
        job_name=job_name,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    total = service.count_events(
        db=session,
        job_name=job_name,
        event_type=event_type,
    )

    return APIResponseModel(
        result={
            "events": [e.to_api_dict() for e in events],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
        description=f"Found {len(events)} lineage events",
    )


@router.get(
    "/events/{event_id}",
    summary="Get lineage event detail",
    response_model=APIResponseModel,
)
async def get_lineage_event(
    session: SessionDep,
    service: LineageEventServiceDep,
    event_id: int = Path(..., description="Event ID", ge=1),
) -> APIResponseModel:
    """Get detailed information of a specific lineage event."""
    event = service.get_event(db=session, event_id=event_id)
    if not event:
        return APIResponseModel(result=None, description="Event not found")

    return APIResponseModel(
        result=event.to_api_dict(),
        description="Event found",
    )


@router.get(
    "/graph/{snapshot_id}",
    summary="Get lineage graph",
    response_model=APIResponseModel,
)
async def get_lineage_graph(
    session: SessionDep,
    service: LineageEventServiceDep,
    snapshot_id: str = Path(..., description="Snapshot ID"),
) -> APIResponseModel:
    """Get full lineage graph for a snapshot.

    Returns graph with nodes (runs/datasets) and edges (inputs/outputs).
    """
    graph = service.get_lineage_graph(db=session, snapshot_id=snapshot_id)
    return APIResponseModel(
        result=graph,
        description="Lineage graph retrieved",
    )


@router.get(
    "/downstream/{snapshot_id}",
    summary="Get downstream lineage",
    response_model=APIResponseModel,
)
async def get_downstream_lineage(
    session: SessionDep,
    service: LineageEventServiceDep,
    snapshot_id: str = Path(..., description="Snapshot ID"),
) -> APIResponseModel:
    """Get full downstream lineage chain from a snapshot.

    Traces: snapshot → draft → catalog_entry
    """
    graph = service.get_full_downstream(db=session, snapshot_id=snapshot_id)
    return APIResponseModel(
        result=graph,
        description="Downstream lineage retrieved",
    )


@router.get(
    "/upstream/{catalog_entry_id}",
    summary="Get upstream lineage",
    response_model=APIResponseModel,
)
async def get_upstream_lineage(
    session: SessionDep,
    service: LineageEventServiceDep,
    catalog_entry_id: int = Path(..., description="Catalog entry ID", ge=1),
) -> APIResponseModel:
    """Get full upstream lineage chain to a catalog entry.

    Traces: catalog_entry → draft → snapshot → file (reverse)
    """
    graph = service.get_full_upstream(db=session, catalog_entry_id=catalog_entry_id)
    return APIResponseModel(
        result=graph,
        description="Upstream lineage retrieved",
    )


@router.get(
    "/catalog-entries/{catalog_entry_id}",
    summary="Get catalog entry lineage",
    response_model=APIResponseModel,
)
async def get_catalog_entry_lineage(
    session: SessionDep,
    service: LineageEventServiceDep,
    catalog_entry_id: int = Path(..., description="Catalog entry ID", ge=1),
) -> APIResponseModel:
    """Get lineage events for a catalog entry."""
    events = service.get_events_by_catalog_entry(db=session, catalog_entry_id=catalog_entry_id)

    upstream: list[dict[str, Any]] = []
    for e in events:
        context = e.extract_context()
        upstream.append(
            {
                "eventType": e.event_type,
                "job": e.job_name,
                "eventTime": e.event_time.isoformat() if e.event_time else None,
                "snapshotId": context["snapshotId"],
                "draftId": context["draftId"],
            }
        )

    return APIResponseModel(
        result={
            "catalogEntryId": catalog_entry_id,
            "upstream": upstream,
            "eventCount": len(events),
        },
        description=f"Found {len(events)} lineage events for catalog entry",
    )
