"""MetadataSnapshot models for metadata-ingestion app."""

from active_metadata.models import MetadataSnapshotBase
from pydantic import BaseModel


class MetadataSnapshot(MetadataSnapshotBase, table=True):  # type: ignore
    """MetadataSnapshot table model."""

    __tablename__ = "metadata_snapshot"  # type: ignore


class SnapshotCreateRequest(BaseModel):
    """DTO for creating snapshot."""

    payload: str | bytes
    filename: str | None = None
