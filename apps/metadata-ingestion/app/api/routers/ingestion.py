"""Ingestion workflow API endpoints."""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from active_metadata.models import IngestionRunState
from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.ingestion_run.dependencies import IngestionRunServiceDep
from app.src.workflow.dependencies import IngestionWorkflowServiceDep

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"],
    route_class=ExceptionHandlingRoute,
)


@router.post(
    "/store",
    summary="Store Phase: Store metadata payload",
    response_model=APIResponseModel,
)
async def store_metadata(
    session: SessionDep,
    workflow_service: IngestionWorkflowServiceDep,
    file: UploadFile = File(...),
) -> APIResponseModel:
    """Store Phase - persist payload and parse metadata entries.

    Does NOT create draft - call POST /ingestion/draft/{run_id} for Draft Phase.
    """
    content = await file.read()
    result = workflow_service.execute_store_phase(session, content, file.filename)

    return APIResponseModel(
        result={
            "snapshot_id": result.snapshot_id,
            "run_id": result.run_id,
            "metadata_count": result.metadata_count,
            "state": "STORED",
        },
        description="Store phase complete: Metadata stored successfully",
    )


@router.post(
    "/draft/{run_id}",
    summary="Draft Phase: Create catalog draft",
    response_model=APIResponseModel,
)
async def create_draft(
    session: SessionDep,
    workflow_service: IngestionWorkflowServiceDep,
    run_id: int,
) -> APIResponseModel:
    """Draft Phase - create catalog entry draft with mapping.

    Requires prior Store Phase completion (run must be in STORED state).
    """
    result = workflow_service.execute_draft_phase(session, run_id)

    return APIResponseModel(
        result={
            "draft": result.draft.to_api_dict(),
            "run_id": result.run_id,
            "mapping_version": result.mapping_version,
            "state": "DRAFTED",
        },
        description="Draft phase complete: Draft created successfully",
    )


@router.get(
    "/runs",
    summary="List ingestion runs",
    response_model=APIResponseModel,
)
async def list_runs(
    session: SessionDep,
    ingestion_run_service: IngestionRunServiceDep,
    state: Optional[str] = Query(None, description="Filter by state: STORED, DRAFTED, FAILED"),
    limit: int = Query(100, ge=1, le=500),
) -> APIResponseModel:
    """List ingestion runs with optional state filter."""
    if state:
        try:
            state_enum = IngestionRunState(state)
            runs = ingestion_run_service.get_runs_by_state(session, state_enum, limit)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid state: {state}") from e
    else:
        runs = ingestion_run_service.get_all_runs(session, limit)

    return APIResponseModel(
        result={
            "runs": [r.model_dump(mode="json", exclude={"updated_at"}) for r in runs],
            "count": len(runs),
        },
        description=f"Found {len(runs)} ingestion runs",
    )


@router.get(
    "/runs/{run_id}",
    summary="Get ingestion run details",
    response_model=APIResponseModel,
)
async def get_run(
    session: SessionDep,
    ingestion_run_service: IngestionRunServiceDep,
    run_id: int,
) -> APIResponseModel:
    """Get details of a specific ingestion run."""
    run = ingestion_run_service.get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return APIResponseModel(
        result=run.model_dump(mode="json"),
        description=f"Ingestion run {run_id}",
    )
