"""Dependency injection for AgentClient."""

from typing import Annotated

from fastapi import Depends

from app.config import settings
from app.src.agent_client.client import AgentClient


def get_agent_client() -> AgentClient:
    """AgentClient dependency."""
    return AgentClient(
        base_url=settings.AGENT_SERVICE_URL,
        timeout=settings.AGENT_REQUEST_TIMEOUT,
        x_token=settings.X_TOKEN,
    )


AgentClientDep = Annotated[AgentClient, Depends(get_agent_client)]
