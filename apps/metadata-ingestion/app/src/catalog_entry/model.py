import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from active_metadata.models import CatalogEntryBase
from active_metadata.utils import to_str_list
from pydantic import BaseModel
from sqlmodel import Field

KST = timezone(timedelta(hours=9))


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
    ingested_at: Optional[str] = None
    updated_at: Optional[str] = None


class CatalogEntryCreate(BaseModel):
    """카탈로그 생성 DTO"""

    identifier: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_metadata: Dict[str, Any]
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
    raw_metadata: Optional[Dict[str, Any]] = None

    def set_field(self, field_name: str, value: Any):
        """Set field with type coercion"""
        list_fields = ["keyword", "theme"]
        date_fields = ["issued", "modified"]

        if field_name in list_fields:
            value = to_str_list(value)
        elif field_name in date_fields and isinstance(value, str):
            try:
                value = datetime.fromisoformat(value).date()
            except ValueError as e:
                logging.error(f"Parsing date failed. {str(e)}")
                value = None

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
