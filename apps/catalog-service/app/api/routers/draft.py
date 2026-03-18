from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Path, Query

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
    summary="드래프트 목록 조회",
    response_model=APIResponseModel,
)
async def list_drafts(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    snapshot_id: Annotated[
        Optional[str],
        Query(
            title="스냅샷 ID",
            description="특정 스냅샷 ID로 필터링 (UUID 형식)",
            openapi_examples={
                "uuid_example": {
                    "summary": "UUID 예시",
                    "value": "18e6f7bc-5791-488a-bc7b-d78b18e51dcd",
                },
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
                "small": {"summary": "소량 조회", "value": 10},
                "large": {"summary": "대량 조회", "value": 100},
            },
        ),
    ] = 100,
    offset: Annotated[
        int,
        Query(
            ge=0,
            title="결과 시작 위치",
            description="검색 결과 시작 위치 (0부터 시작, 페이징에 사용)",
            openapi_examples={
                "first_page": {"summary": "첫 페이지", "value": 0},
                "second_page": {"summary": "두 번째 페이지 (limit=100)", "value": 100},
            },
        ),
    ] = 0,
) -> APIResponseModel:
    """카탈로그 엔트리 드래프트 목록을 조회합니다.

    스냅샷 ID로 필터링하거나 전체 드래프트 목록을 페이징하여 조회합니다."""
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
        description=f"총 {len(drafts)}건 조회",
    )


@router.get(
    "/entries/{draft_id}",
    summary="드래프트 상세 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 ID의 드래프트가 존재하지 않음"},
    },
)
async def get_draft(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    draft_id: int = Path(
        title="드래프트 ID",
        description="조회할 드래프트의 고유 식별 번호",
        example=1,
        ge=1,
    ),
) -> APIResponseModel:
    """특정 드래프트의 상세 정보를 조회합니다.

    매핑 증거(mapping evidence)를 포함한 전체 드래프트 정보를 반환합니다."""
    draft = draft_service.get_draft(session, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    return APIResponseModel(
        result=draft.to_api_dict(),
        description=f"드래프트 {draft_id} 조회 완료",
    )


@router.get(
    "/entries/{draft_id}/evidence",
    summary="매핑 증거 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 ID의 드래프트가 존재하지 않음"},
    },
)
async def get_draft_evidence(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    draft_id: int = Path(
        title="드래프트 ID",
        description="매핑 증거를 조회할 드래프트의 고유 식별 번호",
        example=1,
        ge=1,
    ),
) -> APIResponseModel:
    """드래프트의 매핑 증거만 조회합니다.

    각 필드별 후보(candidates), 추천(recommended), 결정(decided) 정보를 반환합니다."""
    draft = draft_service.get_draft(session, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    return APIResponseModel(
        result={
            "draft_id": draft_id,
            "mapping_evidence": draft.mapping_evidence,
        },
        description=f"드래프트 {draft_id} 매핑 증거 조회 완료",
    )
