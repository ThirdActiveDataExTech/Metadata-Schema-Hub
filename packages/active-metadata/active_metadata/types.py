"""Custom types for metadata management."""

__all__ = ["SnapshotIdentifier", "EntityURI"]

import hashlib
import re
import time
from datetime import UTC, datetime
from functools import cached_property
from typing import ClassVar, Self

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


class SnapshotIdentifier(str):
    """Snapshot identifier value object with full hash support.

    Format: urn:{namespace}:metadata:{timestamp}-{hash[:12]}
    Example: urn:wisenut:metadata:1234567890-abcdef123456

    When created via generate(), stores the full 64-char payload_sha256.
    When created from string, payload_sha256 is None.
    """

    __slots__ = ("_payload_sha256", "__dict__")

    SHA256_HEX_LENGTH: ClassVar[int] = 64
    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^urn:([a-zA-Z0-9_-]+):metadata:(\d+)-([0-9a-fA-F]{12})$")
    # group(1)=namespace, group(2)=timestamp, group(3)=hash_prefix

    def __new__(cls, value: str, payload_sha256: str | None = None) -> "SnapshotIdentifier":
        """Create SnapshotIdentifier from URN string.

        Args:
            value: Snapshot ID in URN format
            payload_sha256: Optional full 64-char SHA256 hash (from generate())

        Raises:
            ValueError: If value doesn't match expected URN format
        """
        if not cls.PATTERN.match(value):
            raise ValueError(
                f"Invalid snapshot_id format: {value}. "
                "Expected: urn:{{namespace}}:metadata:{{timestamp}}-{{hash12}}"
            )
        instance = super().__new__(cls, value)
        # Store payload_sha256 in slot
        object.__setattr__(instance, "_payload_sha256", payload_sha256)
        return instance

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: type, _handler: GetCoreSchemaHandler) -> CoreSchema:
        """Pydantic v2 schema for validation and serialization."""
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema: CoreSchema, _handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        """OpenAPI schema with pattern."""
        return {
            "type": "string",
            "pattern": cls.PATTERN.pattern,
            "description": "Snapshot ID in URN format: urn:{namespace}:metadata:{timestamp}-{hash12}",
            "example": "urn:wisenut:metadata:1234567890-abcdef123456",
        }

    @classmethod
    def _validate(cls, v: str) -> "SnapshotIdentifier":
        """Validate and convert string to SnapshotIdentifier."""
        if isinstance(v, cls):
            return v
        return cls(v)

    @classmethod
    def generate(
        cls,
        payload: str | bytes,
        namespace: str = "wisenut",
        timestamp: int | None = None,
    ) -> Self:
        """Generate SnapshotIdentifier from payload.

        Args:
            payload: Content to generate identifier for
            namespace: URN namespace (default: "wisenut")
            timestamp: Unix timestamp (default: current time)

        Returns:
            New SnapshotIdentifier with full payload_sha256
        """
        payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
        ts = timestamp if timestamp is not None else int(time.time())
        full_hash = hashlib.sha256(payload_bytes).hexdigest()
        return cls(f"urn:{namespace}:metadata:{ts}-{full_hash[:12]}", payload_sha256=full_hash)

    @property
    def payload_sha256(self) -> str | None:
        """Full 64-char SHA256 hash (available only when created via generate())."""
        return getattr(self, "_payload_sha256", None)

    @cached_property
    def _parsed(self) -> re.Match[str]:
        """Cached regex match result."""
        match = self.PATTERN.match(self)
        if not match:
            raise ValueError("Invalid snapshot_id")  # Should never happen after __new__
        return match

    @property
    def snapshot_id(self) -> str:
        """Return the snapshot_id string (self)."""
        return str(self)

    @property
    def namespace(self) -> str:
        """Extract namespace from ID."""
        return self._parsed.group(1)

    @property
    def timestamp(self) -> int:
        """Extract Unix timestamp from ID."""
        return int(self._parsed.group(2))

    @property
    def hash_prefix(self) -> str:
        """Extract 12-char hash prefix from ID."""
        return self._parsed.group(3)

    @property
    def datetime_utc(self) -> datetime:
        """Convert timestamp to UTC datetime."""
        return datetime.fromtimestamp(self.timestamp, tz=UTC)

    def generate_storage_key(self, extension: str) -> str:
        """Generate storage_key path from identifier.

        Returns:
            "{YYYY}/{MM}/{DD}/{timestamp}-{hash[:12]}.{ext}"
        """
        dt = self.datetime_utc
        return f"{dt.year}/{dt.month:02d}/{dt.day:02d}/{self.timestamp}-{self.hash_prefix}.{extension}"


class EntityURI:
    """Entity URI reference helper for lineage tracking.

    URI 형식: {schema}.{table}/{id}
    예: public.metadata_snapshot/abc123, public.catalog_entry_draft/7
    """

    SCHEMA: str = "public"

    @classmethod
    def snapshot(cls, snapshot_id: str, schema: str = SCHEMA) -> str:
        """MetadataSnapshot URI 생성."""
        return f"{schema}.metadata_snapshot/{snapshot_id}"

    @classmethod
    def entry(cls, entry_id: int, schema: str = SCHEMA) -> str:
        """MetadataEntry URI 생성."""
        return f"{schema}.metadata_entry/{entry_id}"

    @classmethod
    def draft(cls, draft_id: int, schema: str = SCHEMA) -> str:
        """CatalogEntryDraft URI 생성."""
        return f"{schema}.catalog_entry_draft/{draft_id}"

    @classmethod
    def catalog(cls, catalog_id: int, schema: str = SCHEMA) -> str:
        """CatalogEntry URI 생성."""
        return f"{schema}.catalog_entry/{catalog_id}"

    @staticmethod
    def file(filename: str) -> str:
        """File URI 생성."""
        return f"file://{filename}"

    @staticmethod
    def parse(uri: str) -> tuple[str, str, str]:
        """URI를 (schema, table, id)로 파싱.

        Args:
            uri: 파싱할 URI 문자열

        Returns:
            ("", "file", filename) for file:// URIs
            (schema, table, id) for {schema}.{table}/{id} URIs

        Examples:
            >>> EntityURI.parse("file://dataset.json")
            ("", "file", "dataset.json")
            >>> EntityURI.parse("public.metadata_snapshot/abc123")
            ("public", "metadata_snapshot", "abc123")
        """
        if uri.startswith("file://"):
            return ("", "file", uri[7:])
        schema_table, entity_id = uri.rsplit("/", 1)
        schema, table = schema_table.split(".", 1)
        return (schema, table, entity_id)
