import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlmodel import Column, Field, SQLModel

from app.src.util.util import to_str_list

KST = timezone(timedelta(hours=9))


class CatalogEntry(SQLModel, table=True):  # pyright: ignore
    """CatalogEntry 모델."""
    __tablename__: str = "catalog_entry"  # pyright: ignore

    id: Optional[int] = Field(
        default=None, primary_key=True
    )
    title: Optional[str] = None
    description: Optional[str] = None
    issued: Optional[date] = None
    modified: Optional[date] = None
    identifier: str = Field(
        nullable=False,
        default_factory=lambda: str(uuid.uuid4())
    )
    publisher: Optional[str] = None
    keyword: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String))
    )
    landing_page: Optional[str] = None
    theme: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String))
    )
    access_url: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False)
    )
    ingested_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )

    @classmethod
    def get_list_fields(cls) -> List[str]:
        """List[str] 타입인 필드명들을 반환

        Returns:
            List[str]: List[str] 타입으로 정의된 필드명 목록

        Note:
            컬럼 변경시 직접 변경 필요
        """
        return ["keyword", "theme"]


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
        """Set field."""
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
