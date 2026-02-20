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

    def get_rdf_dict(self) -> dict[str, Any]:
        """catalog_entry 를 DCAT 기반의 json-ld 로 변환하여 반환"""
        # TODO: validation 필요, 표준 - DCAT-AP Validator, 커스텀 - SHACL

        # 1. Dataset 정보 (원본 데이터의 메타데이터)
        dataset = {
            "@type": "dcat:Dataset",
            "@id": f"urn:dataset:{self.identifier}"
        }

        # DCAT Dataset 필수/권장 속성들
        if self.title:
            dataset["dct:title"] = self.title

        if self.description:
            dataset["dct:description"] = self.description

        if self.identifier:
            dataset["dct:identifier"] = self.identifier

        if self.publisher:
            dataset["dct:publisher"] = {
                "@type": "foaf:Agent",
                "foaf:name": self.publisher
            }

        if self.issued:
            try:
                dataset["dct:issued"] = {
                    "@type": "xsd:date",
                    "@value": self.issued.isoformat()
                }
            except AttributeError:
                # fallback: 타입 명시 없이 문자열로만 처리
                dataset["dct:issued"] = str(self.issued)


        if self.modified:
            try:
                dataset["dct:modified"] = {
                    "@type": "xsd:date",
                    "@value": self.modified.isoformat()
                }
            except AttributeError:
                dataset["dct:modified"] = str(self.modified)

        if self.keyword:
            dataset["dcat:keyword"] = self.keyword

        if self.theme:
            dataset["dcat:theme"] = self.theme

        if self.landing_page:
            dataset["dcat:landingPage"] = {
                "@type": "@id",
                "@id": self.landing_page
            }

        # DCAT Distribution 정보 (access_url이 있을 경우)
        if self.access_url:
            dataset["dcat:distribution"] = {
                "@type": "dcat:Distribution",
                "@id": f"urn:distribution:{self.identifier}",
                "dcat:accessURL": {
                    "@type": "@id",
                    "@id": self.access_url
                }
            }

        # 2. CatalogRecord 정보 (카탈로그 시스템의 관리 정보)
        catalog_record = {
            "@type": "dcat:CatalogRecord",
            "@id": f"urn:catalog-record:{self.identifier}",
            "foaf:primaryTopic": {
                "@id": f"urn:dataset:{self.identifier}"
            }
        }

        if self.ingested_at:
            catalog_record["dct:issued"] = {
                "@type": "xsd:dateTime",
                "@value": self.ingested_at.isoformat()
            }

        if self.updated_at:
            catalog_record["dct:modified"] = {
                "@type": "xsd:dateTime",
                "@value": self.updated_at.isoformat()
            }

        # 3. 전체 구조 반환 (@graph 패턴 사용)
        result = {
            "@context": {
                "dcat": "http://www.w3.org/ns/dcat#",
                "dct": "http://purl.org/dc/terms/",
                "foaf": "http://xmlns.com/foaf/0.1/",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            },
            "@graph": [dataset, catalog_record]
        }

        return result


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
