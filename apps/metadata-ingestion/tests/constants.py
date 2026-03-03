"""Test constants for deterministic, readable tests.

All ID constants follow actual production formats:
- snapshot_id / metadata_id: URN format (urn:wisenut:metadata:{timestamp}-{hash})
- identifier: UUID4 format (default_factory)

Usage:
    from tests.constants import SNAPSHOT_ID_VALID, METADATA_ID_1
"""

# =============================================================================
# Snapshot IDs (URN format: urn:wisenut:metadata:{timestamp}-{hash})
# =============================================================================

# Valid URN formats - matches SnapshotIdentifier.generate() output
SNAPSHOT_ID_VALID = "urn:wisenut:metadata:1708675200-a1b2c3d4e5f6"
SNAPSHOT_ID_VALID_ALT = "urn:wisenut:metadata:1705312800-f6e5d4c3b2a1"

# Invalid formats - for error handling tests
SNAPSHOT_ID_INVALID_SHORT = "snap-123"
SNAPSHOT_ID_INVALID_NO_URN = "abc123"
SNAPSHOT_ID_INVALID_FORMAT = "invalid-snapshot"

# =============================================================================
# Metadata IDs (= snapshot_id in production, URN format)
# =============================================================================

METADATA_ID_1 = "urn:wisenut:metadata:1708675200-094fdfd8f7f8"
METADATA_ID_2 = "urn:wisenut:metadata:1708675200-01b290cc634e"
METADATA_ID_3 = "urn:wisenut:metadata:1708675200-192aa8be09e5"
METADATA_IDS_BULK = [METADATA_ID_1, METADATA_ID_2, METADATA_ID_3]

# =============================================================================
# Catalog Entry Identifiers (UUID4 format - matches default_factory)
# =============================================================================

ENTRY_ID_1 = "4e6cc9f3-88c0-47a1-a4ca-bf93c3f73bef"
ENTRY_ID_2 = "b3e55522-b190-4643-83d2-dbead59a644e"
ENTRY_ID_3 = "22b77f66-3649-439e-a440-407055706fae"
ENTRY_IDS_BULK = [ENTRY_ID_1, ENTRY_ID_2, ENTRY_ID_3]

# =============================================================================
# Fixed Values for Determinism
# =============================================================================

TEST_TIMESTAMP = 1708675200
TEST_MAPPING_VERSION = "v1.0"
TEST_MAPPING_VERSION_ALT = "v1.1"
TEST_SHA256 = "a" * 64
TEST_SHA256_ALT = "b" * 64

# =============================================================================
# Nonexistent IDs (for error handling tests)
# =============================================================================

NONEXISTENT_ID = 99999
NONEXISTENT_IDENTIFIER = "nonexistent"
NONEXISTENT_SNAPSHOT_ID = "urn:wisenut:metadata:9999999999-nonexistent"
