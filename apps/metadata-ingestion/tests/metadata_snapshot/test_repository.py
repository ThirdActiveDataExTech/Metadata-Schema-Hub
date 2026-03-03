"""Integration tests for MetadataSnapshotRepository."""

import pytest
from sqlmodel import Session

from active_metadata.types import SnapshotIdentifier
from app.src.metadata_snapshot.model import MetadataSnapshot
from app.src.metadata_snapshot.repository import MetadataSnapshotRepository
from tests.constants import NONEXISTENT_SNAPSHOT_ID, TEST_SHA256


class TestSave:
    """Tests for save method."""

    def test_save_snapshot(
        self,
        db: Session,
        metadata_snapshot_repository: MetadataSnapshotRepository,
    ) -> None:
        """Should save snapshot."""
        snapshot = MetadataSnapshot(
            snapshot_id=SnapshotIdentifier("urn:wisenut:metadata:1700000000-c1c2c3c4c5c6"),
            payload_sha256="c" * 64,
            storage_key="2024/new/snapshot.json",
            original_filename="new.json",
        )

        result = metadata_snapshot_repository.save(db, snapshot)

        assert str(result.snapshot_id) == "urn:wisenut:metadata:1700000000-c1c2c3c4c5c6"


class TestFindBySnapshotId:
    """Tests for find_by_snapshot_id method."""

    def test_find_existing(
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
        assert result.storage_key == snapshot.storage_key

    def test_find_nonexistent(
        self,
        db: Session,
        metadata_snapshot_repository: MetadataSnapshotRepository,
    ) -> None:
        """Should return None when not found."""
        result = metadata_snapshot_repository.find_by_snapshot_id(
            db, NONEXISTENT_SNAPSHOT_ID
        )
        assert result is None


class TestFindLatestByHash:
    """Tests for find_latest_by_hash method."""

    def test_find_by_hash(
        self,
        db: Session,
        metadata_snapshot_repository: MetadataSnapshotRepository,
        sample_metadata_snapshots: list[MetadataSnapshot],
    ) -> None:
        """Should return snapshot matching hash."""
        target_snapshot = sample_metadata_snapshots[0]
        result = metadata_snapshot_repository.find_latest_by_hash(
            db, target_snapshot.payload_sha256
        )

        assert result is not None
        assert result.payload_sha256 == target_snapshot.payload_sha256

    def test_find_nonexistent_hash(
        self,
        db: Session,
        metadata_snapshot_repository: MetadataSnapshotRepository,
    ) -> None:
        """Should return None for non-existent hash."""
        nonexistent_hash = "z" * 64
        result = metadata_snapshot_repository.find_latest_by_hash(db, nonexistent_hash)
        assert result is None

    def test_find_latest_among_duplicates(
        self,
        db: Session,
        metadata_snapshot_repository: MetadataSnapshotRepository,
    ) -> None:
        """Should return most recent snapshot for duplicate hash."""
        # Create two snapshots with same hash
        snapshot1 = MetadataSnapshot(
            snapshot_id=SnapshotIdentifier("urn:wisenut:metadata:1700000001-d1d2d3d4d5d6"),
            payload_sha256="d" * 64,
            storage_key="2024/first.json",
        )
        snapshot2 = MetadataSnapshot(
            snapshot_id=SnapshotIdentifier("urn:wisenut:metadata:1700000002-e1e2e3e4e5e6"),
            payload_sha256="d" * 64,
            storage_key="2024/second.json",
        )

        metadata_snapshot_repository.save(db, snapshot1)
        metadata_snapshot_repository.save(db, snapshot2)

        result = metadata_snapshot_repository.find_latest_by_hash(db, "d" * 64)

        # Should return the most recently ingested
        assert result is not None
        assert result.storage_key == snapshot2.storage_key
