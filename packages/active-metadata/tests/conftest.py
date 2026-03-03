"""Shared test fixtures and constants."""

from datetime import date

import pytest

# =============================================================================
# Realistic test data based on sample/ directory
# =============================================================================

# Dublin Core / DCAT metadata schemas (actual standards)
METADATA_SCHEMAS = {
    "title": "dct:title",
    "description": "dct:description",
    "modified": "dct:modified",
    "publisher": "dct:publisher",
    "keyword": "dcat:keyword",
    "theme": "dcat:theme",
    "landing_page": "dcat:landingPage",
}

# Sample catalog entry data (from sample/schema_org_15107742.json)
SAMPLE_CATALOG_ENTRY = {
    "title": "전국태양광발전소전기사업허가정보표준데이터",
    "description": "신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법 및 지방자치단체 조례 등에 따라 설치된 태양광 설비 정보",
    "publisher": "지방자치단체",
    "keyword": ["에너지", "태양광", "전기사업"],
    "theme": ["산업·통상·중소기업", "에너지및자원개발"],
    "landing_page": "https://www.data.go.kr/data/15107742/standard.do",
    "issued": date(2024, 9, 25),
    "modified": date(2024, 9, 25),
}

# Valid snapshot_id examples
VALID_SNAPSHOT_IDS = [
    "urn:wisenut:metadata:1708675200-a1b2c3d4e5f6",
    "urn:datagoKr:metadata:1735689600-fedcba987654",
    "urn:my-org:metadata:1640000000-000000000000",
    "urn:my_org:metadata:1640000000-ffffffffffff",
]

# Invalid snapshot_id examples with descriptions
INVALID_SNAPSHOT_IDS = {
    "missing_urn_prefix": "invalid:wisenut:metadata:1708675200-a1b2c3d4e5f6",
    "missing_dash": "urn:wisenut:metadata:1708675200a1b2c3d4e5f6",
    "non_numeric_timestamp": "urn:wisenut:metadata:notanumber-a1b2c3d4e5f6",
    "short_hash": "urn:wisenut:metadata:1708675200-abc",
    "long_hash": "urn:wisenut:metadata:1708675200-a1b2c3d4e5f6789",
    "non_hex_hash": "urn:wisenut:metadata:1708675200-ghijklmnopqr",
    "invalid_namespace_char": "urn:my@org:metadata:1708675200-a1b2c3d4e5f6",
    "wrong_resource_type": "urn:wisenut:catalog:1708675200-a1b2c3d4e5f6",
}

# Valid SHA256 hashes (64 hex chars)
VALID_SHA256_HASHES = [
    "a" * 64,
    "0123456789abcdef" * 4,
    "ABCDEF0123456789" * 4,  # uppercase
]

# Sample file content for extension detection
SAMPLE_CONTENT = {
    "xml": '<?xml version="1.0" encoding="UTF-8"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF>',
    "rdf": '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF>',
    "json_object": '{"@context":"https://schema.org","@type":"Dataset","name":"테스트"}',
    "json_array": '[{"id":1},{"id":2}]',
    "binary": b"\x00\x01\x02\x03",
    "plain_text": "일반 텍스트",
}


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_metadata_entry():
    """Provide sample metadata entry data."""
    return {
        "metadata_schema": METADATA_SCHEMAS["title"],
        "value": SAMPLE_CATALOG_ENTRY["title"],
        "metadata_id": "15107742",
    }


@pytest.fixture
def sample_catalog_entry():
    """Provide sample catalog entry data."""
    return SAMPLE_CATALOG_ENTRY.copy()


@pytest.fixture
def valid_snapshot_id():
    """Provide a valid snapshot_id."""
    return VALID_SNAPSHOT_IDS[0]


@pytest.fixture
def valid_sha256():
    """Provide a valid SHA256 hash."""
    return VALID_SHA256_HASHES[0]
