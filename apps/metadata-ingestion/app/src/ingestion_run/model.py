"""IngestionRun models for metadata-ingestion app."""

from active_metadata.models import IngestionRunBase
from pydantic import BaseModel


class IngestionRun(IngestionRunBase, table=True):  # type: ignore[call-arg]
    """IngestionRun table model."""

    __tablename__ = "ingestion_run"  # type: ignore[assignment]


class IngestionRunCreate(BaseModel):
    """DTO for creating ingestion run (TX1)."""

    snapshot_id: str
    mapping_version: str
