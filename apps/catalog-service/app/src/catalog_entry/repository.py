import json
from datetime import date, datetime
from typing import List, Literal, Optional

from sqlalchemy import and_, or_
from sqlmodel import Session, select

from app.src.catalog_entry.exceptions import CatalogEntryNotFoundError
from app.src.catalog_entry.model import CatalogEntry, CatalogEntrySummary


class CatalogEntryRepository:
    """카탈로그 엔트리 저장소 클래스."""

    ALLOWED_SORT_FIELDS = {
        "title": CatalogEntry.title,
        "issued": CatalogEntry.issued,
        "modified": CatalogEntry.modified,
        "ingested_at": CatalogEntry.ingested_at,
        "updated_at": CatalogEntry.updated_at,
    }

    DATE_FIELD_MAP = {
        "issued": CatalogEntry.issued,
        "modified": CatalogEntry.modified,
        "ingested_at": CatalogEntry.ingested_at,
        "updated_at": CatalogEntry.updated_at,
    }

    def select(self, db: Session, catalog_entry_id: int) -> CatalogEntry:
        """Select catalog_entry."""
        catalog_entry = db.get(CatalogEntry, catalog_entry_id)
        if not catalog_entry:
            raise CatalogEntryNotFoundError(catalog_entry_id=catalog_entry_id)

        return catalog_entry

    def select_by_identifier(self, db: Session, catalog_entry_identifier: str) -> CatalogEntry:
        """Select catalog_entry by identifier."""
        stmt = select(CatalogEntry).where(CatalogEntry.identifier == catalog_entry_identifier)
        catalog_entry = db.exec(stmt).first()
        if not catalog_entry:
            raise CatalogEntryNotFoundError(catalog_entry_id=-1, result={"identifier": catalog_entry_identifier})
        return catalog_entry

    def select_by_ids(self, db: Session, catalog_entry_ids: List[int]) -> List[CatalogEntry]:
        """Select multiple catalog entries by ids."""
        stmt = select(CatalogEntry).where(CatalogEntry.id.in_(catalog_entry_ids))  # pyright: ignore
        return list(db.exec(stmt).all())

    def select_by_identifiers(self, db: Session, catalog_entry_identifiers: List[str]) -> List[CatalogEntry]:
        """Select catalog entries by identifiers."""
        stmt = select(CatalogEntry).where(CatalogEntry.identifier.in_(catalog_entry_identifiers))  # pyright: ignore
        return list(db.exec(stmt).all())

    def select_summaries_by_identifiers(
        self, db: Session, catalog_entry_identifiers: List[str]
    ) -> List[CatalogEntrySummary]:
        """Select catalog entry summaries by identifiers."""
        statement = select(  # pyright: ignore
            CatalogEntry.id,
            CatalogEntry.title,
            CatalogEntry.issued,
            CatalogEntry.modified,
            CatalogEntry.identifier,
            CatalogEntry.publisher,
            CatalogEntry.keyword,
            CatalogEntry.landing_page,
            CatalogEntry.theme,
            CatalogEntry.access_url,
            CatalogEntry.ingested_at,
            CatalogEntry.updated_at,
        ).where(CatalogEntry.identifier.in_(catalog_entry_identifiers))  # pyright: ignore

        rows = db.exec(statement).all()

        return [
            CatalogEntrySummary(
                id=row.id,
                title=row.title,
                issued=str(row.issued) if row.issued else None,
                modified=str(row.modified) if row.modified else None,
                identifier=row.identifier,
                publisher=row.publisher,
                keyword=row.keyword,
                landing_page=row.landing_page,
                theme=row.theme,
                access_url=row.access_url,
                ingested_at=str(row.ingested_at) if row.ingested_at else None,
                updated_at=str(row.updated_at) if row.updated_at else None,
            )
            for row in rows
        ]

    def export_data_list(self, db: Session, limit: int = None):
        """데이터베이스의 catalog_entry 테이블 전체를 list로 내보냄."""
        # 모든 레코드 조회 쿼리 작성 (필요시 limit 추가)
        statement = select(CatalogEntry)
        if limit:
            statement = statement.limit(limit)

        # 쿼리 실행
        results = db.exec(statement).all()

        if not results:
            print("내보낼 데이터가 없습니다.")
            return None

        # 결과를 딕셔너리 리스트로 변환
        data_list = []
        for result in results:
            # SQLModel 0.0.14부터 dict() 대신 model_dump() 사용
            data = result.model_dump()

            # 날짜 필드 문자열 변환
            if "issued" in data and data["issued"]:
                data["issued"] = str(data["issued"])

            if "modified" in data and data["modified"]:
                data["modified"] = str(data["modified"])

            if "ingested_at" in data and data["ingested_at"]:
                data["ingested_at"] = str(data["ingested_at"])

            if "updated_at" in data and data["updated_at"]:
                data["updated_at"] = str(data["updated_at"])

            # JSONB 필드는 문자열로 변환하여 CSV에 저장
            if "publisher" in data and isinstance(data["publisher"], dict):
                data["publisher"] = json.dumps(data["publisher"], ensure_ascii=False)

            if "raw_metadata" in data:
                # raw_metadata는 너무 크고 복잡하므로 CSV에서 제외
                data.pop("raw_metadata", None)

            # 배열 타입 필드 (keyword, theme)도 문자열로 변환
            if "keyword" in data and isinstance(data["keyword"], list):
                data["keyword"] = ",".join(data["keyword"]) if data["keyword"] else ""

            if "theme" in data and isinstance(data["theme"], list):
                data["theme"] = ",".join(data["theme"]) if data["theme"] else ""

            data_list.append(data)

        return data_list

    def list_catalog_summary(self, db: Session, limit: Optional[int] = None) -> List[CatalogEntrySummary]:
        """요약된 카탈로그 목록 조회."""
        statement = select(  # type: ignore
            CatalogEntry.id,
            CatalogEntry.title,
            CatalogEntry.issued,
            CatalogEntry.modified,
            CatalogEntry.identifier,
            CatalogEntry.publisher,
            CatalogEntry.keyword,
            CatalogEntry.landing_page,
            CatalogEntry.theme,
            CatalogEntry.access_url,
            CatalogEntry.ingested_at,
            CatalogEntry.updated_at,
        )

        # Default sorting: most recently updated first
        statement = statement.order_by(CatalogEntry.id.desc())  # type: ignore

        if limit is not None:
            statement = statement.limit(limit)

        rows = db.exec(statement).all()

        return [
            CatalogEntrySummary(
                id=row.id,
                title=row.title,
                issued=str(row.issued) if row.issued else None,
                modified=str(row.modified) if row.modified else None,
                identifier=row.identifier,
                publisher=row.publisher,
                keyword=row.keyword,
                landing_page=row.landing_page,
                theme=row.theme,
                access_url=row.access_url,
                ingested_at=str(row.ingested_at) if row.ingested_at else None,
                updated_at=str(row.updated_at) if row.updated_at else None,
            )
            for row in rows
        ]

    def search_catalog(
        self,
        db: Session,
        query: Optional[str] = None,
        keyword: List[str] = [],
        theme: List[str] = [],
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
        statement = select(  # type: ignore
            CatalogEntry.id,
            CatalogEntry.title,
            CatalogEntry.issued,
            CatalogEntry.modified,
            CatalogEntry.identifier,
            CatalogEntry.publisher,
            CatalogEntry.keyword,
            CatalogEntry.landing_page,
            CatalogEntry.theme,
            CatalogEntry.access_url,
            CatalogEntry.ingested_at,
            CatalogEntry.updated_at,
        )
        conditions = []

        # 텍스트 검색 (제목, 설명에서 ILIKE 검색)
        if query:
            text_condition = or_(
                CatalogEntry.title.ilike(f"%{query}%"),  # type: ignore
                CatalogEntry.description.ilike(f"%{query}%"),  # type: ignore
            )
            conditions.append(text_condition)

        # 키워드 필터 (PostgreSQL 배열 컬럼에서 ANY 검색, OR 조건)
        if keyword:
            keyword_conditions = [CatalogEntry.keyword.any(kw) for kw in keyword]  # type: ignore
            conditions.append(or_(*keyword_conditions))

        # 주제 필터 (PostgreSQL 배열 컬럼에서 ANY 검색, OR 조건)
        if theme:
            theme_conditions = [CatalogEntry.theme.any(t) for t in theme]  # type: ignore
            conditions.append(or_(*theme_conditions))

        # 날짜 범위 필터 (단일 필드 선택 방식)
        if date_field and date_field in self.DATE_FIELD_MAP:
            column = self.DATE_FIELD_MAP[date_field]

            # datetime 필드의 경우 date를 datetime으로 변환
            if date_field in ("ingested_at", "updated_at"):
                if date_from:
                    # date의 시작 시간 (00:00:00)으로 변환
                    datetime_from = datetime.combine(date_from, datetime.min.time())
                    conditions.append(column >= datetime_from)  # type: ignore
                if date_to:
                    # date의 종료 시간 (23:59:59.999999)으로 변환
                    datetime_to = datetime.combine(date_to, datetime.max.time())
                    conditions.append(column <= datetime_to)  # type: ignore
            else:
                # date 필드는 그대로 사용
                if date_from:
                    conditions.append(column >= date_from)  # type: ignore
                if date_to:
                    conditions.append(column <= date_to)  # type: ignore

        # 조건 적용
        if conditions:
            where_condition = and_(*conditions)
            statement = statement.where(where_condition)

        # 정렬 조건 적용 (tie-breaker 포함)
        order_columns = []

        if sort_field and sort_field in self.ALLOWED_SORT_FIELDS:
            column = self.ALLOWED_SORT_FIELDS[sort_field]
            if sort_order == "asc":
                order_columns.append(column.asc())
            else:
                order_columns.append(column.desc())
        else:
            # 기본 정렬: 최근 업데이트 순
            order_columns.append(CatalogEntry.updated_at.desc())  # type: ignore

        # 안정적 정렬을 위해 id를 tie-breaker로 추가 (최신순)
        order_columns.append(CatalogEntry.id.desc())  # type: ignore

        statement = statement.order_by(*order_columns)

        # 페이지네이션 적용
        statement = statement.offset(offset).limit(limit)

        # 결과 조회
        rows = db.exec(statement).all()

        return [
            CatalogEntrySummary(
                id=row.id,
                title=row.title,
                issued=str(row.issued) if row.issued else None,
                modified=str(row.modified) if row.modified else None,
                identifier=row.identifier,
                publisher=row.publisher,
                keyword=row.keyword,
                landing_page=row.landing_page,
                theme=row.theme,
                access_url=row.access_url,
                ingested_at=str(row.ingested_at) if row.ingested_at else None,
                updated_at=str(row.updated_at) if row.updated_at else None,
            )
            for row in rows
        ]
