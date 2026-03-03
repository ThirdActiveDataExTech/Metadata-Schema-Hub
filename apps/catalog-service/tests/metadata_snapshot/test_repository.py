"""Integration tests for MetadataSnapshotRepository."""

import pytest
from sqlmodel import Session

from app.src.metadata_snapshot.model import MetadataSnapshot
from app.src.metadata_snapshot.repository import MetadataSnapshotRepository


class TestFindBySnapshotId:
    """Tests for find_by_snapshot_id method."""

    def test_find_existing_snapshot(
        self,
        db: Session,
        metadata_snapshot_repository: MetadataSnapshotRepository,
        sample_metadata_snapshots: list[MetadataSnapshot],
    ) -> None:
        """Should return snapshot when found."""
        snapshot = sample_metadata_snapshots[0]
        result = metadata_snapshot_repository.find_by_snapshot_id(
            db, str(snapshot.snapshot_id)
        )

        assert result is not None
        assert str(result.snapshot_id) == str(snapshot.snapshot_id)
        assert result.storage_key == snapshot.storage_key

    def test_find_nonexistent_returns_none(
        self,
        db: Session,
        metadata_snapshot_repository: MetadataSnapshotRepository,
    ) -> None:
        """Should return None for non-existent snapshot_id."""
        result = metadata_snapshot_repository.find_by_snapshot_id(
            db, "urn:wisenut:metadata:1234567890-nonexistent"
        )
        assert result is None

    def test_find_with_different_snapshots(
        self,
        db: Session,
        metadata_snapshot_repository: MetadataSnapshotRepository,
        sample_metadata_snapshots: list[MetadataSnapshot],
    ) -> None:
        """Should find correct snapshot among multiple."""
        snapshot1 = sample_metadata_snapshots[0]
        snapshot2 = sample_metadata_snapshots[1]

        result1 = metadata_snapshot_repository.find_by_snapshot_id(
            db, str(snapshot1.snapshot_id)
        )
        result2 = metadata_snapshot_repository.find_by_snapshot_id(
            db, str(snapshot2.snapshot_id)
        )

        assert result1 is not None
        assert result2 is not None
        assert result1.original_filename == snapshot1.original_filename
        assert result2.original_filename == snapshot2.original_filename
