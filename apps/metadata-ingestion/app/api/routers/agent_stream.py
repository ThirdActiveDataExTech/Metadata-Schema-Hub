"""SSE streaming endpoints for agent integration (read-only proxy).

Pure SSE passthrough — no DB writes during streaming.
Frontend receives final_response, then calls existing sync endpoints to apply.
Does NOT use ExceptionHandlingRoute (errors → SSE error events).
"""

import json

from active_metadata.agent_schemas import (
    AvailableMetadataItem,
    DraftMappingRequest,
    MappingEvidence,
    MergeAnalysisRequest,
    MergeEvidence,
)
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.config import settings
from app.db import engine
from app.dependencies import get_token_header
from app.src.agent_client.dependencies import AgentClientDep
from app.src.catalog_entry_draft.dependencies import CatalogEntryDraftServiceDep
from app.src.catalog_merge.dependencies import CatalogMergeServiceDep
from app.src.metadata_entry.dependencies import MetadataEntryServiceDep

router = APIRouter(
    tags=["agent-stream"],
    dependencies=[Depends(get_token_header)],
)


def _check_agent_enabled() -> None:
    if not settings.AGENT_ENABLED:
        raise HTTPException(status_code=503, detail="Agent integration is disabled.")


@router.post(
    "/draft/entries/{draft_id}/regen/stream",
    summary="에이전트 드래프트 재생성 스트리밍 (읽기 전용)",
    responses={404: {}, 503: {}},
)
async def regen_draft_fields_stream(
    draft_service: CatalogEntryDraftServiceDep,
    metadata_service: MetadataEntryServiceDep,
    agent_client: AgentClientDep,
    draft_id: int = Path(title="드래프트 ID", ge=1),
) -> StreamingResponse:
    """에이전트 SSE 이벤트를 프록시합니다. DB write 없음.

    final_response 수신 후 프론트엔드가 PATCH /draft/entries/{id} 로 결과를 적용합니다.
    """
    _check_agent_enabled()

    with Session(engine) as session:
        draft = draft_service.get_draft(session, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

        metadata_entries = metadata_service.select_metadata(session, draft.snapshot_id)

        agent_request = DraftMappingRequest(
            draft_id=draft_id,
            snapshot_id=str(draft.snapshot_id),
            mapping_evidence={k: v for k, v in draft.mapping_evidence.items()},
            available_metadata=[
                AvailableMetadataItem(metadata_schema=e.metadata_schema, value=e.value) for e in metadata_entries
            ],
        )

    async def event_generator():
        async for event in agent_client.stream_draft_mapping(agent_request):
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
            if event.get("type") == "error":
                return

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post(
    "/merge/entries/{merge_id}/regen/stream",
    summary="에이전트 머지 재분석 스트리밍 (읽기 전용)",
    responses={404: {}, 503: {}},
)
async def regen_merge_analysis_stream(
    merge_service: CatalogMergeServiceDep,
    draft_service: CatalogEntryDraftServiceDep,
    agent_client: AgentClientDep,
    merge_id: int = Path(title="머지 ID", ge=1),
) -> StreamingResponse:
    """에이전트 SSE 이벤트를 프록시합니다. DB write 없음.

    final_response 수신 후 프론트엔드가 approve/reject 엔드포인트로 결과를 적용합니다.
    """
    _check_agent_enabled()

    with Session(engine) as session:
        merge = merge_service.get_merge(session, merge_id)
        if not merge:
            raise HTTPException(status_code=404, detail=f"CatalogMerge {merge_id} not found")

        draft = draft_service.get_draft(session, merge.draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail=f"Draft {merge.draft_id} not found")

        merge_evidence = MergeEvidence.model_validate(merge.merge_evidence)
        draft_mapping_evidence = {k: MappingEvidence.model_validate(v) for k, v in draft.mapping_evidence.items()}

        agent_request = MergeAnalysisRequest(
            merge_id=merge_id,
            draft_id=merge.draft_id,
            mapping_score=merge.mapping_score,
            merge_evidence=merge_evidence,
            draft_mapping_evidence=draft_mapping_evidence,
        )

    async def event_generator():
        async for event in agent_client.stream_merge_analysis(agent_request):
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
            if event.get("type") == "error":
                return

    return StreamingResponse(event_generator(), media_type="text/event-stream")
