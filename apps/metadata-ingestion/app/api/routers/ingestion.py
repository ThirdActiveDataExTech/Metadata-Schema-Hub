from typing import Annotated, Optional
from uuid import UUID

from active_metadata.models import IngestionRunState
from fastapi import APIRouter, File, HTTPException, Path, Query, UploadFile

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
    summary="Store Phase: 메타데이터 저장",
    response_model=APIResponseModel,
    responses={
        400: {"description": "파일 읽기 실패 또는 지원하지 않는 파일 형식"},
        422: {"description": "파일 파싱 실패"},
    },
)
async def store_metadata(
    session: SessionDep,
    workflow_service: IngestionWorkflowServiceDep,
    file: UploadFile = File(
        title="메타데이터 파일",
        description="수집할 메타데이터 파일 (.json, .jsonld, .xml, .rdf)",
    ),
) -> APIResponseModel:
    """메타데이터 파일을 저장하고 파싱합니다 (Store Phase).

    파일을 업로드하면 스냅샷을 생성하고 메타데이터 엔트리로 파싱합니다.
    드래프트 생성은 별도로 POST /ingestion/draft/{run_id}를 호출해야 합니다.
    """
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 읽기 실패: {str(e)}") from e

    result = workflow_service.execute_store_phase(session, content, file.filename)

    return APIResponseModel(
        result={
            "snapshot_id": result.snapshot_id,
            "run_id": result.run_id,
            "metadata_count": result.metadata_count,
            "state": IngestionRunState.STORED,
        },
        description=f"Store Phase 완료: 메타데이터 {result.metadata_count}건 저장",
    )


@router.post(
    "/draft/{run_id}",
    summary="Draft Phase: 카탈로그 드래프트 생성",
    response_model=APIResponseModel,
    responses={
        400: {"description": "잘못된 상태 (STORED 상태가 아님)"},
        404: {"description": "해당 run_id의 수집 실행이 존재하지 않음"},
    },
)
async def create_draft(
    session: SessionDep,
    workflow_service: IngestionWorkflowServiceDep,
    run_id: UUID = Path(
        title="수집 실행 ID",
        description="드래프트를 생성할 수집 실행의 UUID",
        example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
    ),
) -> APIResponseModel:
    """카탈로그 엔트리 드래프트를 생성합니다 (Draft Phase).

    Store Phase가 완료된 수집 실행(STORED 상태)에 대해 드래프트를 생성합니다.
    컬럼 관계 기반 자동 매핑이 적용됩니다.
    """
    result = workflow_service.execute_draft_phase(session, run_id)

    return APIResponseModel(
        result={
            "draft": result.draft.to_api_dict(),
            "mapping_version": result.mapping_version,
            "state": IngestionRunState.DRAFTED,
        },
        description=f"Draft Phase 완료: 드래프트 {result.draft.id} 생성",
    )


@router.post(
    "/merge/{draft_id}",
    summary="Merge Phase: 엔티티 매칭 + 자동 발행 판단",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 draft_id의 드래프트가 존재하지 않음"},
    },
)
async def execute_merge(
    session: SessionDep,
    workflow_service: IngestionWorkflowServiceDep,
    draft_id: int = Path(
        title="드래프트 ID",
        description="머지를 실행할 드래프트의 ID",
        ge=1,
    ),
) -> APIResponseModel:
    """드래프트에 대해 머지 단계를 실행합니다 (Merge Phase).

    엔티티 매칭, 스코어링을 수행하고 score >= threshold이면 자동 발행합니다.
    score < threshold이면 PENDING 상태로 수동 리뷰를 대기합니다.
    """
    result = workflow_service.execute_merge_phase(session, draft_id)

    return APIResponseModel(
        result={
            "merge": result.merge.model_dump(),
            "auto_published": result.auto_published,
            "catalog_entry_id": result.catalog_entry_id,
        },
        description=(
            f"Merge Phase 완료: 머지 {result.merge.id} 생성"
            + (f", 카탈로그 엔트리 {result.catalog_entry_id} 자동 발행" if result.auto_published else ", 수동 리뷰 대기")
        ),
    )


@router.get(
    "/runs",
    summary="수집 실행 목록 조회",
    response_model=APIResponseModel,
)
async def list_runs(
    session: SessionDep,
    ingestion_run_service: IngestionRunServiceDep,
    state: Annotated[
        Optional[str],
        Query(
            title="상태 필터",
            description="수집 실행 상태로 필터링 (STORED, DRAFTED, FAILED)",
            openapi_examples={
                "stored": {"summary": "저장 완료", "value": "STORED"},
                "drafted": {"summary": "드래프트 생성 완료", "value": "DRAFTED"},
                "failed": {"summary": "실패", "value": "FAILED"},
            },
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=500,
            title="결과 제한",
            description="검색 결과 최대 개수",
            openapi_examples={
                "small": {"summary": "소량 조회", "value": 20},
                "large": {"summary": "대량 조회", "value": 100},
            },
        ),
    ] = 100,
) -> APIResponseModel:
    """수집 실행 목록을 조회합니다.

    상태별 필터링 또는 전체 목록을 조회합니다.
    """
    if state:
        try:
            state_enum = IngestionRunState(state)
            runs = ingestion_run_service.get_runs_by_state(session, state_enum, limit)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"잘못된 상태 값: {state}") from e
    else:
        runs = ingestion_run_service.get_all_runs(session, limit)

    return APIResponseModel(
        result={
            "runs": [r.model_dump(mode="json", exclude={"updated_at"}) for r in runs],
            "count": len(runs),
        },
        description=f"수집 실행 {len(runs)}건 조회",
    )


@router.get(
    "/runs/{run_id}",
    summary="수집 실행 상세 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 run_id의 수집 실행이 존재하지 않음"},
    },
)
async def get_run(
    session: SessionDep,
    ingestion_run_service: IngestionRunServiceDep,
    run_id: UUID = Path(
        title="수집 실행 ID",
        description="조회할 수집 실행의 UUID",
        example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
    ),
) -> APIResponseModel:
    """특정 수집 실행의 상세 정보를 조회합니다.

    수집 실행의 상태, 스냅샷 ID, 드래프트 ID 등 전체 정보를 반환합니다.
    """
    run = ingestion_run_service.get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"수집 실행 {run_id}을(를) 찾을 수 없습니다")

    return APIResponseModel(
        result=run.model_dump(mode="json"),
        description=f"수집 실행 {run_id} 조회 완료",
    )
