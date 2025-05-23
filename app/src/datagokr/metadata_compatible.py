import os
import pathlib
import tempfile
from pathlib import Path

import pandas as pd

from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.catalog_entry.service import CatalogEntryService
from app.src.datagokr.config import config
from app.src.datagokr.extractor import download_metadata, get_dcat, get_openschema_org
from app.src.dcat.dcat_processor import parse_dcat_xml
from app.src.schema_org.schema_org_processor import parse_schema_org_json
from app.src.util.util import ensure_directory, sample_data

repository = CatalogEntryRepository()
service = CatalogEntryService(repository)


def process_openschema(list_id, list_type="standard", result_path: str | Path = config.SAMPLE_DIR):
    """OpenSchema.org 메타데이터 처리 및 데이터베이스 저장 함수"""
    if not list_id:
        raise Exception(f"처리할 {list_id}가 필요합니다.")

    # OpenSchema.org 메타데이터 다운로드 및 처리
    openschema_path = get_openschema_org(list_id, list_type, result_path)
    if not openschema_path:
        raise Exception(f"OpenSchema 메타데이터를 찾을 수 없습니다: {list_id}")

    openschema_data = parse_schema_org_json(openschema_path)
    if not openschema_data:
        raise Exception(f"OpenSchema 메타데이터 파싱 실패: {list_id}")

    openschema_id = service.import_to_database(openschema_data)
    if openschema_id:
        print(f"OpenSchema 메타데이터 저장 완료 (ID: {openschema_id})")
        return openschema_id
    else:
        raise Exception(f"OpenSchema 메타데이터 저장 실패: {list_id}")


def process_dcat(list_id, result_path: str | Path):
    """DCAT 메타데이터 처리 및 데이터베이스 저장 함수"""
    if not list_id:
        raise Exception(f"처리할 {list_id=}가 필요합니다.")

    # DCAT 메타데이터 다운로드 및 처리
    dcat_path = get_dcat(list_id, result_path)
    if not dcat_path:
        raise Exception(f"DCAT 메타데이터를 찾을 수 없습니다: {list_id}")

    dcat_data = parse_dcat_xml(dcat_path)
    if not dcat_data:
        raise Exception(f"DCAT 메타데이터 파싱 실패: {list_id}")

    dcat_id = service.import_to_database(dcat_data)
    if dcat_id:
        print(f"DCAT 메타데이터 저장 완료 (ID: {dcat_id})")
        return dcat_id
    else:
        raise Exception(f"DCAT 메타데이터 저장 실패: {list_id}")


def process_metadata(
        list_id, list_type="standard", result_path: str | Path = config.SAMPLE_DIR, process_type="all"
):
    """메타데이터 처리 및 데이터베이스 저장 통합 함수"""
    if not list_id:
        raise Exception(f"처리할 {list_id=}가 필요합니다.")

    results = {}

    # 처리 유형에 따라 필요한 메타데이터만 처리
    if process_type.lower() == "all" or process_type.lower() == "openschema":
        openschema_id = process_openschema(list_id, list_type, result_path)
        results["openschema_id"] = openschema_id

    if process_type.lower() == "all" or process_type.lower() == "dcat":
        dcat_id = process_dcat(list_id, result_path)
        results["dcat_id"] = dcat_id

    return results


# 실행 예제
if __name__ == "__main__":
    # 경로 설정
    current_path = pathlib.Path(__file__)
    project_root = current_path.parent.parent.parent.parent  # 4단계 상위로 이동
    sample_path = project_root / "sample"

    ensure_directory(sample_path)

    list_path = os.path.join(sample_path, "standard_list.parquet")

    # 임시 디렉토리 생성하여 작업
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. 데이터 샘플링 및 임시 파일 저장
        list_sample_path = sample_data(list_path, temp_dir)

        # 2. 파일 경로로부터 데이터프레임 읽기
        list_df = pd.read_parquet(list_sample_path)

        # 3. 샘플 데이터에서 ID 추출
        list_id_1 = list_df["list_id"].iloc[0]
        list_id_2 = list_df["list_id"].iloc[1]
        list_id_3 = list_df["list_id"].iloc[2]

        # 4. 메타데이터 저장
        list_id_1_openschema, list_id_1_dcat = download_metadata(list_id_1, "standard", sample_path)
        list_id_2_openschema, list_id_2_dcat = download_metadata(list_id_2, "standard", sample_path)
        list_id_3_openschema, list_id_3_dcat = download_metadata(list_id_3, "standard", sample_path)

        # 예제 2: 단일 ID 처리
        # 모든 형식 처리
        results = process_metadata(list_id=list_id_1, list_type="standard")
        print(f"처리 결과: {results}")

        # 특정 형식만 처리
        openschema_result = process_metadata(
            list_id=list_id_2, list_type="standard", result_path=sample_path, process_type="openschema"
        )
        print(f"OpenSchema 처리 결과: {openschema_result}")

        dcat_result = process_metadata(
            list_id=list_id_3, list_type="standard", result_path=sample_path, process_type="dcat"
        )
        print(f"DCAT 처리 결과: {dcat_result}")

    # 예제 3: 메타데이터 CSV 내보내기
    metadata_csv_path = os.path.join(sample_path, "all_catalog_entries.csv")

    csv_path = service.export_to_csv(metadata_csv_path)
    print(f"내보낸 CSV 파일 경로: {csv_path}")
