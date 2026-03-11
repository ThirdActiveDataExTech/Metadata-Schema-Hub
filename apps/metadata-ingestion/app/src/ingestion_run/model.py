"""IngestionRun models for metadata-ingestion app."""

from uuid import UUID

from active_metadata.models import IngestionRunBase
from pydantic import BaseModel


class IngestionRun(IngestionRunBase, table=True):  # type: ignore[call-arg]
    """IngestionRun table model."""

    __tablename__ = "ingestion_run"  # type: ignore[assignment]


class IngestionRunCreate(BaseModel):
    """DTO for creating ingestion run (TX1)."""

    run_id: UUID
    snapshot_id: str
    mapping_version: str
