import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from active_metadata import CatalogEntryBase, parse_date, to_atomic_list, to_str_list
from pydantic import BaseModel
from sqlmodel import Field


class CatalogEntry(CatalogEntryBase, table=True):  # pyright: ignore
    """CatalogEntry table model."""

    __tablename__: str = "catalog_entry"  # pyright: ignore


class CatalogEntrySummary(BaseModel):
    """카탈로그 목록 응답 DTO"""

    id: int
    title: Optional[str] = None
    issued: Optional[str] = None
    modified: Optional[str] = None
    identifier: str
    publisher: Optional[str] = None
    keyword: Optional[List[str]] = None
    landing_page: Optional[str] = None
    theme: Optional[List[str]] = None
    access_url: Optional[str] = None
    external_ids: Optional[List[str]] = None
    ingested_at: Optional[str] = None
    updated_at: Optional[str] = None


class CatalogEntryCreate(BaseModel):
    """카탈로그 생성 DTO"""

    identifier: str = Field(default_factory=lambda: str(uuid.uuid4()))
    latest_snapshot_id: Optional[str] = None
    ingested_at: datetime = Field(default_factory=datetime.now)


class CatalogEntryUpdate(BaseModel):
    """카탈로그 업데이트 DTO"""

    title: Optional[str] = None
    description: Optional[str] = None
    issued: Optional[date] = None
    modified: Optional[date] = None
    publisher: Optional[str] = None
    keyword: Optional[List[str]] = None
    landing_page: Optional[str] = None
    theme: Optional[List[str]] = None
    access_url: Optional[str] = None
    external_ids: Optional[List[str]] = None
    latest_snapshot_id: Optional[str] = None

    def set_field(self, field_name: str, value: Any):
        """Set field with type coercion."""
        if field_name in CatalogEntryBase.get_list_fields():
            value = to_str_list(value)
        elif field_name in CatalogEntryBase.get_atomic_list_fields():
            value = to_atomic_list(value)
        elif field_name in CatalogEntryBase.get_date_fields():
            value = parse_date(value)
        setattr(self, field_name, value)

    def model_dump_for_update(self) -> Dict[str, Any]:
        """업데이트용 딕셔너리 반환 (None 값 제외)"""
        return self.model_dump(exclude_none=True)

    def has_changes(self) -> bool:
        """변경사항 존재 여부"""
        return len(self.model_dump_for_update()) > 0

    def apply_to_catalog_entry(self, catalog_entry: CatalogEntry) -> CatalogEntry:
        """기존 CatalogEntry에 업데이트 적용"""
        update_data = self.model_dump_for_update()
        for field, value in update_data.items():
            setattr(catalog_entry, field, value)
        return catalog_entry
