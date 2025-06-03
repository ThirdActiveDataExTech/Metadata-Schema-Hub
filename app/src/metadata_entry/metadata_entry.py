from dataclasses import dataclass


@dataclass
class MetadataEntry:
    """메타데이터 flatten 테이블."""
    id: int | None
    metadata_id: str | None
    metadata_schema: str
    value: str
