from typing import Annotated, Any

from active_metadata.models import LineageEventType
from fastapi import APIRouter, Path, Query

from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.lineage.dependencies import LineageEventServiceDep

router = APIRouter(prefix="/lineage", tags=["lineage"], route_class=ExceptionHandlingRoute)


@router.get(
    "/events",
    summary="리니지 이벤트 목록 조회",
    response_model=APIResponseModel,
)
async def list_lineage_events(
    session: SessionDep,
    service: LineageEventServiceDep,
    job_name: Annotated[
        str | None,
        Query(
            title="작업명 필터",
            description="특정 작업명으로 필터링",
            openapi_examples={
                "ingest": {"summary": "수집 작업", "value": "metadata_ingest"},
                "transform": {"summary": "변환 작업", "value": "catalog_transform"},
            },
        ),
    ] = None,
    event_type: Annotated[
        LineageEventType | None,
        Query(
            title="이벤트 유형 필터",
            description="리니지 이벤트 유형으로 필터링 (START, COMPLETE, FAIL 등)",
            openapi_examples={
                "complete": {"summary": "완료 이벤트", "value": "COMPLETE"},
                "start": {"summary": "시작 이벤트", "value": "START"},
            },
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=200,
            title="결과 제한",
            description="검색 결과 최대 개수",
            openapi_examples={
                "small": {"summary": "소량 조회", "value": 20},
                "large": {"summary": "대량 조회", "value": 100},
            },
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
            title="결과 시작 위치",
            description="검색 결과 시작 위치 (0부터 시작, 페이징에 사용)",
            openapi_examples={
                "first_page": {"summary": "첫 페이지", "value": 0},
                "second_page": {"summary": "두 번째 페이지 (limit=50)", "value": 50},
            },
        ),
    ] = 0,
) -> APIResponseModel:
    """리니지 이벤트 목록을 조회합니다.

    작업명, 이벤트 유형으로 필터링하거나 전체 이벤트 목록을 페이징하여 조회합니다."""
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
        description=f"리니지 이벤트 {len(events)}건 조회 (전체 {total}건)",
    )


@router.get(
    "/events/{event_id}",
    summary="리니지 이벤트 상세 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 ID의 리니지 이벤트가 존재하지 않음"},
    },
)
async def get_lineage_event(
    session: SessionDep,
    service: LineageEventServiceDep,
    event_id: int = Path(
        title="이벤트 ID",
        description="조회할 리니지 이벤트의 고유 식별 번호",
        example=1,
        ge=1,
    ),
) -> APIResponseModel:
    """특정 리니지 이벤트의 상세 정보를 조회합니다.

    이벤트의 입력/출력 데이터셋, 실행 컨텍스트 등 전체 정보를 반환합니다."""
    event = service.get_event(db=session, event_id=event_id)
    if not event:
        return APIResponseModel(result=None, description="이벤트를 찾을 수 없습니다")

    return APIResponseModel(
        result=event.to_api_dict(),
        description=f"리니지 이벤트 {event_id} 조회 완료",
    )


@router.get(
    "/graph/{snapshot_id}",
    summary="리니지 그래프 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 스냅샷 ID의 리니지 정보가 존재하지 않음"},
    },
)
async def get_lineage_graph(
    session: SessionDep,
    service: LineageEventServiceDep,
    snapshot_id: str = Path(
        title="스냅샷 ID",
        description="리니지 그래프를 조회할 스냅샷의 UUID",
        example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
    ),
) -> APIResponseModel:
    """스냅샷의 전체 리니지 그래프를 조회합니다.

    노드(runs/datasets)와 엣지(inputs/outputs)로 구성된 그래프를 반환합니다."""
    graph = service.get_lineage_graph(db=session, snapshot_id=snapshot_id)
    return APIResponseModel(
        result=graph,
        description="리니지 그래프 조회 완료",
    )


@router.get(
    "/downstream/{snapshot_id}",
    summary="다운스트림 리니지 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 스냅샷 ID의 리니지 정보가 존재하지 않음"},
    },
)
async def get_downstream_lineage(
    session: SessionDep,
    service: LineageEventServiceDep,
    snapshot_id: str = Path(
        title="스냅샷 ID",
        description="다운스트림 리니지를 조회할 스냅샷의 UUID",
        example="18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
    ),
) -> APIResponseModel:
    """스냅샷에서 시작하는 전체 다운스트림 리니지 체인을 조회합니다.

    추적 방향: snapshot → draft → catalog_entry"""
    graph = service.get_full_downstream(db=session, snapshot_id=snapshot_id)
    return APIResponseModel(
        result=graph,
        description="다운스트림 리니지 조회 완료",
    )


@router.get(
    "/upstream/{catalog_entry_id}",
    summary="업스트림 리니지 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 카탈로그 엔트리 ID의 리니지 정보가 존재하지 않음"},
    },
)
async def get_upstream_lineage(
    session: SessionDep,
    service: LineageEventServiceDep,
    catalog_entry_id: int = Path(
        title="카탈로그 엔트리 ID",
        description="업스트림 리니지를 조회할 카탈로그 엔트리의 고유 식별 번호",
        example=1,
        ge=1,
    ),
) -> APIResponseModel:
    """카탈로그 엔트리로 향하는 전체 업스트림 리니지 체인을 조회합니다.

    추적 방향: catalog_entry ← draft ← snapshot ← file (역방향)"""
    graph = service.get_full_upstream(db=session, catalog_entry_id=catalog_entry_id)
    return APIResponseModel(
        result=graph,
        description="업스트림 리니지 조회 완료",
    )


@router.get(
    "/catalog-entries/{catalog_entry_id}",
    summary="카탈로그 엔트리 리니지 이벤트 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 카탈로그 엔트리 ID의 리니지 정보가 존재하지 않음"},
    },
)
async def get_catalog_entry_lineage(
    session: SessionDep,
    service: LineageEventServiceDep,
    catalog_entry_id: int = Path(
        title="카탈로그 엔트리 ID",
        description="리니지 이벤트를 조회할 카탈로그 엔트리의 고유 식별 번호",
        example=1,
        ge=1,
    ),
) -> APIResponseModel:
    """카탈로그 엔트리와 관련된 리니지 이벤트를 조회합니다.

    해당 카탈로그 엔트리 생성에 관여한 모든 리니지 이벤트를 반환합니다."""
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
        description=f"카탈로그 엔트리 {catalog_entry_id}의 리니지 이벤트 {len(events)}건 조회",
    )
