"""MetadataSnapshot models for catalog-service (read-only)."""

from active_metadata.models import MetadataSnapshotBase


class MetadataSnapshot(MetadataSnapshotBase, table=True):  # type: ignore
    """MetadataSnapshot table model (read-only access)."""

    __tablename__ = "metadata_snapshot"  # type: ignore
