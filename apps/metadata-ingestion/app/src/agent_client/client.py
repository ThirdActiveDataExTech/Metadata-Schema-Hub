"""HTTP client for the external LangGraph agent service."""

from __future__ import annotations

import logging

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
