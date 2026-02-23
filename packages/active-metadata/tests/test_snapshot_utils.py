"""Unit tests for snapshot utilities."""

import time

from active_metadata.snapshot_utils import (
    SnapshotIdentifier,
    detect_extension,
    generate_snapshot_identifier,
)


def test_generate_snapshot_identifier_structure():
    """Test SnapshotIdentifier structure and fields."""
    payload = b"test content"
    identifier = generate_snapshot_identifier(payload)

    # Check type
    assert isinstance(identifier, SnapshotIdentifier)

    # Check fields exist
    assert hasattr(identifier, "snapshot_id")
    assert hasattr(identifier, "timestamp")
    assert hasattr(identifier, "payload_sha256")

    # Check field types
    assert isinstance(identifier.snapshot_id, str)
    assert isinstance(identifier.timestamp, int)
    assert isinstance(identifier.payload_sha256, str)


def test_generate_snapshot_identifier_format():
    """Test snapshot_id format."""
    payload = b"test content"
    identifier = generate_snapshot_identifier(payload)

    # Check URN format
    assert identifier.snapshot_id.startswith("urn:wisenut:metadata:")

    # Check format: urn:wisenut:metadata:{timestamp}-{hash[:12]}
    parts = identifier.snapshot_id.split(":")
    assert len(parts) == 4
    assert parts[0] == "urn"
    assert parts[1] == "wisenut"
    assert parts[2] == "metadata"

    # Check timestamp-hash part
    timestamp_hash = parts[3]
    assert "-" in timestamp_hash
    timestamp_part, hash_part = timestamp_hash.split("-", 1)
    assert timestamp_part.isdigit()
    assert len(hash_part) == 12


def test_generate_snapshot_identifier_with_string():
    """Test with string payload."""
    payload = "test content"
    identifier = generate_snapshot_identifier(payload)

    assert identifier.snapshot_id.startswith("urn:wisenut:metadata:")
    assert isinstance(identifier.payload_sha256, str)
    assert len(identifier.payload_sha256) == 64  # SHA256 hex length


def test_generate_snapshot_identifier_with_bytes():
    """Test with bytes payload."""
    payload = b"test content"
    identifier = generate_snapshot_identifier(payload)

    assert identifier.snapshot_id.startswith("urn:wisenut:metadata:")
    assert isinstance(identifier.payload_sha256, str)
    assert len(identifier.payload_sha256) == 64


def test_generate_snapshot_identifier_deterministic_hash():
    """Test that same content produces same hash."""
    payload = b"deterministic test"

    id1 = generate_snapshot_identifier(payload)
    time.sleep(1.1)  # Sleep > 1 second to ensure different timestamp
    id2 = generate_snapshot_identifier(payload)

    # Different timestamps (since we slept > 1 second)
    assert id1.timestamp != id2.timestamp
    assert id1.snapshot_id != id2.snapshot_id

    # But same hash
    assert id1.payload_sha256 == id2.payload_sha256


def test_generate_snapshot_identifier_different_content():
    """Test that different content produces different hashes."""
    id1 = generate_snapshot_identifier(b"content 1")
    id2 = generate_snapshot_identifier(b"content 2")

    assert id1.payload_sha256 != id2.payload_sha256
    assert id1.snapshot_id != id2.snapshot_id


def test_generate_storage_key_format():
    """Test storage_key generation format."""
    payload = b"test"
    identifier = generate_snapshot_identifier(payload)

    storage_key = identifier.generate_storage_key("json")

    # Check format: {YYYY}/{MM}/{DD}/{timestamp}-{hash[:12]}.{ext}
    parts = storage_key.split("/")
    assert len(parts) == 4

    # Check date parts
    year, month, day, filename = parts
    assert len(year) == 4 and year.isdigit()
    assert len(month) == 2 and month.isdigit()
    assert len(day) == 2 and day.isdigit()

    # Check filename
    assert filename.endswith(".json")
    assert "-" in filename
    timestamp_part, rest = filename.split("-", 1)
    assert timestamp_part.isdigit()
    assert rest.endswith(".json")


def test_generate_storage_key_utc():
    """Test that storage_key uses UTC timezone."""
    # Create identifier with known timestamp
    identifier = SnapshotIdentifier(
        snapshot_id="urn:wisenut:metadata:1708675200-abcdef123456",
        timestamp=1708675200,  # 2024-02-23 08:00:00 UTC
        payload_sha256="abcdef123456789012345678901234567890123456789012345678901234",
    )

    storage_key = identifier.generate_storage_key("json")

    # Verify UTC date (2024/02/23)
    assert storage_key.startswith("2024/02/23/")


def test_generate_storage_key_with_extension():
    """Test storage_key with different extensions."""
    identifier = SnapshotIdentifier(
        snapshot_id="test",
        timestamp=int(time.time()),
        payload_sha256="a" * 64,
    )

    assert identifier.generate_storage_key("json").endswith(".json")
    assert identifier.generate_storage_key("xml").endswith(".xml")
    assert identifier.generate_storage_key("rdf").endswith(".rdf")
    assert identifier.generate_storage_key("bin").endswith(".bin")


def test_detect_extension_from_filename():
    """Test extension detection from filename."""
    assert detect_extension(b"content", "file.json") == "json"
    assert detect_extension(b"content", "file.xml") == "xml"
    assert detect_extension(b"content", "data.rdf") == "rdf"
    assert detect_extension(b"content", "archive.tar.gz") == "gz"


def test_detect_extension_xml_content():
    """Test XML content detection."""
    xml_content = '<?xml version="1.0"?><root></root>'
    assert detect_extension(xml_content, None) == "xml"

    rdf_content = '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF>'
    assert detect_extension(rdf_content, None) == "xml"


def test_detect_extension_json_content():
    """Test JSON content detection."""
    json_object = '{"key": "value"}'
    assert detect_extension(json_object, None) == "json"

    json_array = '[1, 2, 3]'
    assert detect_extension(json_array, None) == "json"


def test_detect_extension_binary_fallback():
    """Test fallback to 'bin' for unknown content."""
    assert detect_extension(b"\x00\x01\x02", None) == "bin"
    assert detect_extension("plain text", None) == "bin"
    assert detect_extension("", None) == "bin"


def test_detect_extension_with_whitespace():
    """Test content detection with leading/trailing whitespace."""
    json_with_whitespace = '  \n{"key": "value"}\n  '
    assert detect_extension(json_with_whitespace, None) == "json"

    xml_with_whitespace = '  \n<?xml version="1.0"?>\n  '
    assert detect_extension(xml_with_whitespace, None) == "xml"


def test_detect_extension_filename_priority():
    """Test that filename takes priority over content detection."""
    # Even though content looks like JSON, filename should win
    json_content = '{"key": "value"}'
    assert detect_extension(json_content, "data.xml") == "xml"


def test_generate_snapshot_identifier_default_namespace():
    """Test default namespace is 'wisenut'."""
    payload = b"test"
    identifier = generate_snapshot_identifier(payload)
    assert identifier.snapshot_id.startswith("urn:wisenut:metadata:")


def test_generate_snapshot_identifier_custom_namespace():
    """Test custom namespace parameter."""
    payload = b"test"
    identifier = generate_snapshot_identifier(payload, namespace="myorg")
    assert identifier.snapshot_id.startswith("urn:myorg:metadata:")
    assert len(identifier.snapshot_id.split(":")) == 4


def test_generate_snapshot_identifier_namespace_with_hyphens():
    """Test namespace with hyphens."""
    payload = b"test"
    identifier = generate_snapshot_identifier(payload, namespace="my-org")
    assert identifier.snapshot_id.startswith("urn:my-org:metadata:")


def test_generate_snapshot_identifier_namespace_with_underscores():
    """Test namespace with underscores."""
    payload = b"test"
    identifier = generate_snapshot_identifier(payload, namespace="my_org")
    assert identifier.snapshot_id.startswith("urn:my_org:metadata:")
