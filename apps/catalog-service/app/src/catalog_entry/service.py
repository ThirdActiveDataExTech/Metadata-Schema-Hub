import io
from datetime import date
from typing import List, Literal, Optional

import pandas as pd
from sqlmodel import Session

from app.src.catalog_entry.model import CatalogEntry, CatalogEntrySummary
from app.src.catalog_entry.repository import CatalogEntryRepository


class CatalogEntryService:
    """CatalogEntryService."""

    def __init__(self, repository: CatalogEntryRepository):
        """Connect Repository."""
        self.repository = repository

    def get_catalog_entry(self, db: Session, catalog_entry_id: int) -> CatalogEntry:
        """Get Catalog Entry."""
        return self.repository.select(db, catalog_entry_id)

    def get_catalog_entry_by_identifier(self, db: Session, catalog_entry_identifier: str) -> CatalogEntry:
        """Get Catalog Entry."""
        return self.repository.select_by_identifier(db, catalog_entry_identifier)

    def get_catalog_entries(self, db: Session, catalog_entry_ids: List[int]) -> List[CatalogEntry]:
        """Get Catalog Entries."""
        return self.repository.select_by_ids(db, catalog_entry_ids)

    def get_catalog_entries_by_identifier(self, db: Session, catalog_entry_identifiers: List[str]) -> List[CatalogEntry]:
        """Get Catalog Entry."""
        return self.repository.select_by_identifiers(db, catalog_entry_identifiers)

    def get_catalog_entry_summary_by_identifier(
        self, db: Session, catalog_entry_identifiers: List[str]
    ) -> List[CatalogEntrySummary]:
        """Get CatalogEntrySummary."""
        return self.repository.select_summaries_by_identifiers(db, catalog_entry_identifiers)

    def export_to_csv_stream(self, db: Session, limit: int = 100) -> io.StringIO:
        """메모리에서 CSV 스트림 생성"""
        data_list = self.repository.export_data_list(db, limit=limit)
        df = pd.DataFrame(data_list)

        # StringIO로 메모리에서 CSV 생성
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding="utf-8")
        csv_buffer.seek(0)

        return csv_buffer

    def list_catalog(self, db: Session, limit: Optional[int] = None) -> List[CatalogEntrySummary]:
        """전체 카탈로그 목록 조회.

        Args:
            db: 데이터베이스 세션
            limit: 조회할 최대 개수

        Returns:
            카탈로그 엔트리 요약 목록
        """
        return self.repository.list_catalog_summary(db, limit=limit)

    def search_catalog(
        self,
        db: Session,
        query: Optional[str] = None,
        keyword: Optional[List[str]] = None,
        theme: Optional[List[str]] = None,
        date_field: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        offset: int = 0,
        limit: int = 10,
        sort_field: Optional[str] = None,
        sort_order: Optional[Literal["asc", "desc"]] = None,
    ) -> List[CatalogEntrySummary]:
        """검색 조건에 따른 카탈로그 엔트리 검색.

        Args:
            db: 데이터베이스 세션
            query: 제목, 설명 텍스트 검색어
            keyword: 키워드 배열 (OR 조건)
            theme: 주제 분류 배열 (OR 조건)
            date_field: 날짜 필터링 대상 필드
            date_from: 날짜 범위 시작일
            date_to: 날짜 범위 종료일
            offset: 검색 결과 시작 위치
            limit: 검색 결과 최대 개수
            sort_field: 정렬 필드
            sort_order: 정렬 방향 (asc 또는 desc)

        Returns:
            카탈로그 엔트리 요약 목록
        """
        return self.repository.search_catalog(
            db=db,
            query=query,
            keyword=keyword,
            theme=theme,
            date_field=date_field,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit,
            sort_field=sort_field,
            sort_order=sort_order,
        )
