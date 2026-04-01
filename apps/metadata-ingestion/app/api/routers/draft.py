from typing import Annotated, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query

from app.dependencies import SessionDep
from app.handlers import ExceptionHandlingRoute
from app.schemas.response import APIResponseModel
from app.src.catalog_entry_draft.dependencies import CatalogEntryDraftServiceDep
from app.src.catalog_entry_draft.examples import DRAFT_UPDATE_EXAMPLES
from app.src.catalog_entry_draft.model import DraftFieldsUpdateRequest
from app.src.metadata_entry.dependencies import MetadataEntryServiceDep

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

    스냅샷 ID로 필터링하거나 전체 드래프트 목록을 페이징하여 조회합니다.
    결과는 생성일시 기준 내림차순으로 정렬됩니다."""
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


@router.get(
    "/entries/{draft_id}/metadata-options",
    summary="메타데이터 옵션 조회",
    response_model=APIResponseModel,
    responses={
        404: {"description": "해당 ID의 드래프트가 존재하지 않음"},
    },
)
async def get_metadata_options(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    metadata_service: MetadataEntryServiceDep,
    draft_id: int = Path(
        title="드래프트 ID",
        description="메타데이터 옵션을 조회할 드래프트의 고유 식별 번호",
        example=1,
        ge=1,
    ),
) -> APIResponseModel:
    """드래프트 편집에 사용 가능한 메타데이터 엔트리 목록을 조회합니다.

    드래프트의 스냅샷에 포함된 모든 메타데이터 key-value 쌍을 반환합니다.
    사용자가 어떤 카탈로그 필드에 어떤 메타데이터 값을 선택할지 결정할 때 사용합니다."""
    draft = draft_service.get_draft(session, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    entries = metadata_service.select_metadata(session, draft.snapshot_id)

    return APIResponseModel(
        result=[{"schema": e.metadata_schema, "value": e.value} for e in entries],
        description=f"드래프트 {draft_id}에 사용 가능한 메타데이터 {len(entries)}건 조회",
    )


@router.patch(
    "/entries/{draft_id}",
    summary="드래프트 필드 수정",
    response_model=APIResponseModel,
    responses={
        400: {"description": "잘못된 필드명 또는 메타데이터 스키마"},
        404: {"description": "해당 ID의 드래프트가 존재하지 않음"},
    },
)
async def update_draft_fields(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    metadata_service: MetadataEntryServiceDep,
    draft_id: int = Path(
        title="드래프트 ID",
        description="수정할 드래프트의 고유 식별 번호",
        example=1,
        ge=1,
    ),
    request: DraftFieldsUpdateRequest = Body(
        openapi_examples=DRAFT_UPDATE_EXAMPLES,
    ),
) -> APIResponseModel:
    """드래프트 필드를 메타데이터 엔트리에서 선택하여 수정합니다.

    각 업데이트는 카탈로그 필드와 사용할 메타데이터 스키마를 지정합니다.
    매핑 증거의 decided 값도 함께 갱신됩니다."""
    draft = draft_service.get_draft(session, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    metadata_entries = metadata_service.select_metadata(session, draft.snapshot_id)
    updated_draft = draft_service.update_draft_fields(session, draft_id, request.updates, metadata_entries)

    return APIResponseModel(
        result=updated_draft.to_api_dict(),
        description=f"드래프트 {draft_id} 수정 완료 ({len(request.updates)}개 필드)",
    )


@router.post(
    "/entries/{draft_id}/discard",
    summary="드래프트 폐기",
    response_model=APIResponseModel,
    responses={
        400: {"description": "폐기 조건 미충족 (이미 발행됨, 이미 폐기됨 등)"},
        404: {"description": "해당 ID의 드래프트가 존재하지 않음"},
    },
)
async def discard_draft(
    session: SessionDep,
    draft_service: CatalogEntryDraftServiceDep,
    draft_id: int = Path(
        title="드래프트 ID",
        description="폐기할 드래프트의 고유 식별 번호",
        example=1,
        ge=1,
    ),
) -> APIResponseModel:
    """드래프트를 폐기합니다.

    드래프트 상태가 DISCARDED로 변경됩니다.
    이미 발행된 드래프트는 폐기할 수 없습니다."""
    try:
        draft = draft_service.discard(session, draft_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return APIResponseModel(
        result={
            "id": draft.id,
            "status": draft.status,
        },
        description=f"드래프트 {draft_id} 폐기 완료",
    )
