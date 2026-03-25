from typing import List, Optional

from active_metadata.models import CatalogEntryBase
from pydantic import BaseModel


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
