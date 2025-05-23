import datetime
import logging
import os.path
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import xmltodict

from app.schemas.catalog_entry import CatalogEntry
from app.src.catalog_entry.repository import CatalogEntryRepository


class CatalogEntryService:
    """CatalogEntryService."""
    def __init__(self, repository: CatalogEntryRepository):
        """Connect Repository."""
        self.repository = repository

    def import_to_database(self, data: Dict[str, Any]):
        """데이터 전처리하고 Repository 통해 DB 저장"""
        # 빈 identifier인 경우 현재 시간 기반 고유 식별자 생성
        if not data.get("identifier"):
            data["identifier"] = f"generated_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        catalog_entry = CatalogEntry(**data)

        catalog_entry = self.repository.save(catalog_entry)
        return catalog_entry.id

    def get_raw_metadata(self, catalog_entry_id: int, data_format: str = "schema.org") -> Any:
        """Get raw metadata."""
        raw_metadata =  self.repository.select(catalog_entry_id).raw_metadata

        if data_format == "dcat":
            xml_string = xmltodict.unparse(raw_metadata, full_document=True, pretty=True)
            return xml_string

        return raw_metadata


    def export_to_csv(self, output_path: str | Path,  limit: int = None):
        """데이터베이스의 catalog_entry 테이블 전체를 CSV로 내보내기"""
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            raise Exception(f"{output_dir=} not exists.")

        data_list = self.repository.export_data_list(limit=limit)

        # pandas DataFrame으로 변환
        df = pd.DataFrame(data_list)

        # CSV 파일로 저장
        df.to_csv(output_path, index=False, encoding="utf-8-sig")  # BOM 포함 UTF-8로 저장

        logging.info(f"CSV 내보내기 완료: {output_path} (총 {len(data_list)}개 레코드)")
        return output_path


    def insert_data(self, data: List[Dict[str, Any]]):
        """변환된 데이터를 데이터베이스에 삽입합니다."""
        processed_data = []
        for entry in data:
            entry_copy = entry.copy()
            if not entry_copy.get("identifier"):
                entry_copy["identifier"] = f"generated_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            processed_data.append(CatalogEntry(**entry_copy))

        catalog_entries =  self.repository.save_bulk(processed_data)

        print(f"총 {len(catalog_entries)}개의 데이터가 catalog_entry 테이블에 삽입되었습니다.")
