"""HTTP client for the external LangGraph agent service."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

import httpx
import requests
from active_metadata.agent_schemas import (
    DraftMappingRequest,
    DraftMappingResponse,
    MergeAnalysisRequest,
    MergeAnalysisResponse,
)

from app.src.agent_client.exceptions import (
    AgentResponseError,
    AgentTimeoutError,
    AgentUnavailableError,
)

logger = logging.getLogger(__name__)


class AgentClient:
    """Synchronous HTTP client for the external LangGraph agent service.

    Follows the same dependency-injection pattern as other services in this app.
    All calls are synchronous (requests library) — consistent with existing service layer.
    """

    def __init__(self, base_url: str, timeout: int, x_token: str) -> None:
        """Initialise client with base URL, timeout, and auth token."""
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = {
            "Content-Type": "application/json",
            "x-token": x_token,
        }

    def regen_draft_mapping(self, request: DraftMappingRequest) -> DraftMappingResponse:
        """POST /agent/draft/mapping — request agent to re-map draft fields.

        Args:
            request: DraftMappingRequest with mapping_evidence and available_metadata

        Returns:
            DraftMappingResponse with list of DraftFieldUpdate decisions

        Raises:
            AgentUnavailableError: Agent returned HTTP error
            AgentTimeoutError: Request exceeded AGENT_REQUEST_TIMEOUT
            AgentResponseError: Response cannot be parsed into DraftMappingResponse
        """
        url = f"{self._base_url}/agent/draft/mapping"
        logger.info("Calling agent draft mapping: draft_id=%d url=%s", request.draft_id, url)

        try:
            resp = requests.post(
                url,
                data=request.model_dump_json(),
                headers=self._headers,
                timeout=self._timeout,
            )
        except requests.Timeout:
            raise AgentTimeoutError(self._timeout)
        except requests.ConnectionError as e:
            raise AgentUnavailableError(503, str(e))

        if not resp.ok:
            raise AgentUnavailableError(resp.status_code, resp.text)

        try:
            return DraftMappingResponse.model_validate(resp.json())
        except Exception as e:
            raise AgentResponseError(str(e))

    def regen_merge_analysis(self, request: MergeAnalysisRequest) -> MergeAnalysisResponse:
        """POST /agent/merge/analysis — request agent to analyse and decide on merge.

        Args:
            request: MergeAnalysisRequest with merge_evidence and draft context

        Returns:
            MergeAnalysisResponse with decision (approve/reject/defer) and reason

        Raises:
            AgentUnavailableError: Agent returned HTTP error
            AgentTimeoutError: Request exceeded AGENT_REQUEST_TIMEOUT
            AgentResponseError: Response cannot be parsed into MergeAnalysisResponse
        """
        url = f"{self._base_url}/agent/merge/analysis"
        logger.info("Calling agent merge analysis: merge_id=%d url=%s", request.merge_id, url)

        try:
            resp = requests.post(
                url,
                data=request.model_dump_json(),
                headers=self._headers,
                timeout=self._timeout,
            )
        except requests.Timeout:
            raise AgentTimeoutError(self._timeout)
        except requests.ConnectionError as e:
            raise AgentUnavailableError(503, str(e))

        if not resp.ok:
            raise AgentUnavailableError(resp.status_code, resp.text)

        try:
            return MergeAnalysisResponse.model_validate(resp.json())
        except Exception as e:
            raise AgentResponseError(str(e))

    # ── Async streaming methods (SSE proxy) ──────────────────────

    _SSE_TIMEOUT = httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0)

    @staticmethod
    def _error_event(message: str) -> dict:
        return {"type": "error", "node": None, "data": {"message": message}}

    @staticmethod
    def _parse_sse_frames(buffer: str) -> tuple[list[dict], str]:
        """Extract complete SSE frames from *buffer*, return (events, remaining)."""
        events: list[dict] = []
        while "\n\n" in buffer:
            frame, buffer = buffer.split("\n\n", 1)
            for line in frame.strip().split("\n"):
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str:
                    continue
                try:
                    events.append(json.loads(data_str))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse SSE data: %s", data_str)
        return events, buffer

    async def _stream_sse(self, url: str, payload: str) -> AsyncGenerator[dict, None]:
        """Open an SSE stream via httpx and yield parsed event dicts.

        Each yielded dict has the structure:
        ``{"type": "node_complete"|"final_response"|"error", "node": ..., "data": ..., "timestamp": ...}``
        """
        try:
            async with httpx.AsyncClient(timeout=self._SSE_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    url,
                    content=payload,
                    headers=self._headers,
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        yield self._error_event(f"Agent HTTP {response.status_code}: {body.decode()}")
                        return

                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk.replace("\r\n", "\n")
                        events, buffer = self._parse_sse_frames(buffer)
                        for event in events:
                            yield event
        except httpx.ConnectError as e:
            yield self._error_event(f"Agent connection failed: {e}")
        except httpx.ReadTimeout:
            yield self._error_event("Agent stream read timeout")
        except Exception as e:
            yield self._error_event(f"Stream error: {e}")

    async def stream_draft_mapping(self, request: DraftMappingRequest) -> AsyncGenerator[dict, None]:
        """POST /agent/draft/mapping/stream — yield SSE events for draft regen."""
        url = f"{self._base_url}/agent/draft/mapping/stream"
        logger.info("Starting agent draft mapping stream: draft_id=%d url=%s", request.draft_id, url)
        async for event in self._stream_sse(url, request.model_dump_json()):
            yield event

    async def stream_merge_analysis(self, request: MergeAnalysisRequest) -> AsyncGenerator[dict, None]:
        """POST /agent/merge/analysis/stream — yield SSE events for merge analysis."""
        url = f"{self._base_url}/agent/merge/analysis/stream"
        logger.info("Starting agent merge analysis stream: merge_id=%d url=%s", request.merge_id, url)
        async for event in self._stream_sse(url, request.model_dump_json()):
            yield event
