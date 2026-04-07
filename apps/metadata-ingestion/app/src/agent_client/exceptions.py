"""Agent client exceptions."""


class AgentDisabledError(Exception):
    """Raised when AGENT_ENABLED=False and a /regen endpoint is called."""

    def __init__(self) -> None:
        """Initialise with a fixed disabled-integration message."""
        super().__init__("Agent integration is disabled. Set AGENT_ENABLED=True and AGENT_SERVICE_URL.")


class AgentUnavailableError(Exception):
    """Raised when the agent service returns an HTTP error."""

    def __init__(self, status_code: int, detail: str) -> None:
        """Initialise with HTTP status code and detail message."""
        self.status_code = status_code
        super().__init__(f"Agent returned HTTP {status_code}: {detail}")


class AgentTimeoutError(Exception):
    """Raised when the agent service does not respond within the configured timeout."""

    def __init__(self, timeout: int) -> None:
        """Initialise with the timeout duration in seconds."""
        super().__init__(f"Agent request timed out after {timeout}s")


class AgentResponseError(Exception):
    """Raised when the agent response cannot be parsed into the expected schema."""

    def __init__(self, detail: str) -> None:
        """Initialise with a description of the parsing failure."""
        super().__init__(f"Invalid agent response: {detail}")
