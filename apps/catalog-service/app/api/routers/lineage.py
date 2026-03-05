"""Lineage API endpoints for querying OpenLineage events."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Path, Query

from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.lineage.dependencies import LineageEventServiceDep
from app.src.lineage.model import LineageEvent

router = APIRouter(prefix="/lineage", tags=["lineage"], route_class=ExceptionHandlingRoute)


def _extract_filename(event: LineageEvent) -> str | None:
    """Extract original filename from event payload."""
    payload = event.event_payload or {}
    inputs = payload.get("inputs", [])
    if inputs and isinstance(inputs, list) and len(inputs) > 0:
        return inputs[0].get("name")
    return None


def _extract_output_info(event: LineageEvent) -> dict[str, Any]:
    """Extract output info (snapshotId, draftId, catalogEntryId) from payload."""
    payload = event.event_payload or {}
    outputs = payload.get("outputs", [])
    info: dict[str, Any] = {}
    if outputs and isinstance(outputs, list):
        for out in outputs:
            facets = out.get("outputFacets", {})
            if "amm_snapshot" in facets:
                info["snapshotId"] = facets["amm_snapshot"].get("snapshotId")
            if "amm_draft" in facets:
                info["draftId"] = facets["amm_draft"].get("draftId")
            if "amm_catalogEntry" in facets:
                info["catalogEntryId"] = facets["amm_catalogEntry"].get("catalogEntryId")
                info["identifier"] = facets["amm_catalogEntry"].get("identifier")
    return info


@router.get(
    "/events",
    summary="리니지 이벤트 목록 조회",
    response_model=APIResponseModel,
)
async def list_lineage_events(
    session: SessionDep,
    service: LineageEventServiceDep,
    job_name: str | None = Query(None, description="Job 이름 필터 (예: metadata-ingestion.store-phase)"),
    event_type: str | None = Query(None, description="이벤트 타입 필터 (START/COMPLETE/FAIL)"),
    snapshot_id: str | None = Query(None, description="스냅샷 ID 필터"),
    limit: int = Query(50, ge=1, le=200, description="페이지당 결과 수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
) -> APIResponseModel:
    """리니지 이벤트 목록을 조회합니다.

    OpenLineage 표준 형식의 이벤트 목록을 반환합니다.
    """
    events = service.list_events(
        db=session,
        job_name=job_name,
        event_type=event_type,
        snapshot_id=snapshot_id,
        limit=limit,
        offset=offset,
    )
    total = service.count_events(
        db=session,
        job_name=job_name,
        event_type=event_type,
        snapshot_id=snapshot_id,
    )
    return APIResponseModel(
        result={
            "events": [
                {
                    "id": e.id,
                    "eventTime": e.event_time.isoformat(),
                    "eventType": e.event_type,
                    "runId": str(e.run_id),
                    "jobName": e.job_name,
                    "jobNamespace": e.job_namespace,
                    "snapshotId": e.snapshot_id,
                    "draftId": e.draft_id,
                    "catalogEntryId": e.catalog_entry_id,
                    "ingestionRunId": e.ingestion_run_id,
                    "filename": _extract_filename(e),
                }
                for e in events
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
        description=f"Found {len(events)} lineage events",
    )


@router.get(
    "/events/{event_id}",
    summary="리니지 이벤트 상세 조회",
    response_model=APIResponseModel,
)
async def get_lineage_event(
    session: SessionDep,
    service: LineageEventServiceDep,
    event_id: int = Path(..., description="이벤트 ID", ge=1),
) -> APIResponseModel:
    """특정 리니지 이벤트의 상세 정보를 조회합니다.

    전체 OpenLineage RunEvent payload를 포함합니다.
    """
    event = service.get_event(db=session, event_id=event_id)
    if not event:
        return APIResponseModel(result=None, description="Event not found")

    return APIResponseModel(
        result={
            "id": event.id,
            "eventTime": event.event_time.isoformat(),
            "eventType": event.event_type,
            "runId": str(event.run_id),
            "jobName": event.job_name,
            "jobNamespace": event.job_namespace,
            "snapshotId": event.snapshot_id,
            "draftId": event.draft_id,
            "catalogEntryId": event.catalog_entry_id,
            "payload": event.event_payload,  # Full OpenLineage RunEvent
        },
        description="Event found",
    )


@router.get(
    "/runs/{run_id}",
    summary="Run의 이벤트 목록 조회",
    response_model=APIResponseModel,
)
async def get_run_events(
    session: SessionDep,
    service: LineageEventServiceDep,
    run_id: UUID = Path(..., description="OpenLineage Run UUID"),
) -> APIResponseModel:
    """특정 Run의 모든 이벤트를 시간순으로 조회합니다."""
    events = service.get_events_by_run(db=session, run_id=run_id)
    return APIResponseModel(
        result={
            "runId": str(run_id),
            "events": [
                {
                    "id": e.id,
                    "eventTime": e.event_time.isoformat(),
                    "eventType": e.event_type,
                    "jobName": e.job_name,
                }
                for e in events
            ],
            "count": len(events),
        },
        description=f"Found {len(events)} events for run",
    )


@router.get(
    "/graph/{snapshot_id}",
    summary="리니지 그래프 조회",
    response_model=APIResponseModel,
)
async def get_lineage_graph(
    session: SessionDep,
    service: LineageEventServiceDep,
    snapshot_id: str = Path(..., description="기준 스냅샷 ID"),
) -> APIResponseModel:
    """특정 스냅샷의 전체 리니지 그래프를 조회합니다.

    노드(runs)와 엣지(inputs/outputs)로 구성된 그래프를 반환합니다.
    """
    graph = service.get_lineage_graph(db=session, snapshot_id=snapshot_id)
    return APIResponseModel(
        result=graph,
        description="Lineage graph retrieved",
    )


@router.get(
    "/catalog-entries/{catalog_entry_id}",
    summary="카탈로그 엔트리의 리니지 조회",
    response_model=APIResponseModel,
)
async def get_catalog_entry_lineage(
    session: SessionDep,
    service: LineageEventServiceDep,
    catalog_entry_id: int = Path(..., description="카탈로그 엔트리 ID", ge=1),
) -> APIResponseModel:
    """특정 카탈로그 엔트리의 전체 리니지를 조회합니다.

    해당 엔트리를 생성한 모든 워크플로우 이벤트를 반환합니다.
    """
    events = service.get_events_by_catalog_entry(db=session, catalog_entry_id=catalog_entry_id)

    upstream: list[dict[str, Any]] = []
    for e in events:
        upstream.append({
            "eventType": e.event_type,
            "job": e.job_name,
            "runId": str(e.run_id),
            "eventTime": e.event_time.isoformat(),
            "snapshotId": e.snapshot_id,
            "draftId": e.draft_id,
        })

    return APIResponseModel(
        result={
            "catalogEntryId": catalog_entry_id,
            "upstream": upstream,
            "eventCount": len(events),
        },
        description=f"Found {len(events)} lineage events for catalog entry",
    )
