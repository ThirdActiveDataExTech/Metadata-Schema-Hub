"""Snapshot ID generation utilities."""

import hashlib
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class SnapshotIdentifier:
    """Snapshot identifier components."""

    snapshot_id: str
    timestamp: int
    payload_sha256: str

    def generate_storage_key(self, extension: str) -> str:
        """Generate storage_key path from identifier.

        Returns:
            "{YYYY}/{MM}/{DD}/{timestamp}-{hash[:12]}.{ext}"
        """
        dt = datetime.fromtimestamp(self.timestamp, tz=UTC)
        return f"{dt.year}/{dt.month:02d}/{dt.day:02d}/{self.timestamp}-{self.payload_sha256[:12]}.{extension}"


def generate_snapshot_identifier(
    payload: str | bytes,
    namespace: str = "wisenut",
) -> SnapshotIdentifier:
    """Generate snapshot identifier from payload.

    Args:
        payload: Content to generate identifier for
        namespace: URN namespace (default: "wisenut")

    Returns:
        SnapshotIdentifier with snapshot_id, timestamp, and payload_sha256
    """
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload

    timestamp = int(time.time())
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    snapshot_id = f"urn:{namespace}:metadata:{timestamp}-{payload_sha256[:12]}"

    return SnapshotIdentifier(
        snapshot_id=snapshot_id,
        timestamp=timestamp,
        payload_sha256=payload_sha256,
    )


def detect_extension(payload: str | bytes, filename: str | None) -> str:
    """Detect file extension from filename or content."""
    if filename:
        ext = Path(filename).suffix.lstrip(".")
        if ext:
            return ext

    # Content-based detection
    if isinstance(payload, str):
        content = payload.strip()
    else:
        try:
            content = payload.decode("utf-8").strip()
        except Exception:
            return "bin"

    if content.startswith("<?xml") or content.startswith("<rdf:RDF"):
        return "xml"
    elif content.startswith("{") or content.startswith("["):
        return "json"

    return "bin"
