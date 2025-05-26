import json
from typing import List

from sqlalchemy import select
from sqlmodel import select

from app.dependencies import SessionDep
from app.schemas.catalog_entry import CatalogEntry


class CatalogEntryRepository:
    """CatalogEntryService."""

    def save(self, db: SessionDep, catalog_entry: CatalogEntry) -> CatalogEntry:
        """Save catalog_entry."""
        db.add(catalog_entry)
        db.commit()
        db.refresh(catalog_entry)
        return catalog_entry

    def save_bulk(self, db: SessionDep, catalog_entries: List[CatalogEntry]) -> List[CatalogEntry]:
        """Bulk save catalog_entries."""
        if not catalog_entries:
            return []

        db.add_all(catalog_entries)
        db.commit()
        for entry in catalog_entries:
            db.refresh(entry)
        return catalog_entries

    def select(self, db: SessionDep, catalog_entry_id: int) -> CatalogEntry:
        """Select catalog_entry."""
        catalog_entry = db.get(CatalogEntry, catalog_entry_id)
        if not catalog_entry:
            raise ValueError(f"{catalog_entry_id=} not found.")

        return catalog_entry

    def export_data_list(self, db: SessionDep, limit: int = None):
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
