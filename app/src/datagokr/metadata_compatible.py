import json
import os
import pathlib
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlmodel import Session

from app.schemas.catalog_entry import CatalogEntry
from app.src.datagokr.config import config
from app.src.datagokr.dcat_processor import parse_dcat_xml
from app.src.datagokr.extractor import export_to_csv, get_openschema_org, get_dcat, download_metadata
from app.src.datagokr.openschema_processor import parse_openschema_json
from app.src.datagokr.util import sample_data


def import_to_database(data, engine):
    """데이터를 데이터베이스에 삽입 (항상 새 레코드 생성)"""
    if not data or not isinstance(data, dict):
        return None

    try:
        # 필수 필드 확인 및 기본값 설정
        for field in ['byte_size', 'identifier']:
            if field not in data or data[field] is None:
                data[field] = ''

        # 빈 identifier인 경우 현재 시간 기반 고유 식별자 생성
        if not data.get('identifier'):
            data['identifier'] = f"generated_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # JSONB 필드 처리
        if 'publisher' in data:
            if isinstance(data['publisher'], str):
                try:
                    data['publisher'] = json.loads(data['publisher'])
                except json.JSONDecodeError:
                    data['publisher'] = {'name': data['publisher']}

        # raw_metadata 처리
        if 'raw_metadata' in data and isinstance(data['raw_metadata'], str):
            try:
                data['raw_metadata'] = json.loads(data['raw_metadata'])
            except json.JSONDecodeError:
                data['raw_metadata'] = {'raw_data': data['raw_metadata']}

        # SQLModel 인스턴스 생성
        catalog_entry = CatalogEntry(**data)

        # 데이터베이스에 저장
        with Session(engine) as session:
            session.add(catalog_entry)
            session.commit()
            session.refresh(catalog_entry)

            return catalog_entry.id

    except Exception as e:
        print(f"데이터베이스 삽입 오류: {e}")
        return None


def process_openschema(list_id, list_type='standard', db_url=None, result_path: str | Path = config.SAMPLE_DIR):
    """OpenSchema.org 메타데이터 처리 및 데이터베이스 저장 함수"""
    if not list_id:
        raise Exception(f"처리할 {list_id}가 필요합니다.")

    # 데이터베이스 연결
    engine = create_engine(db_url)

    # OpenSchema.org 메타데이터 다운로드 및 처리
    openschema_path = get_openschema_org(list_id, list_type, result_path)
    if not openschema_path:
        raise Exception(f"OpenSchema 메타데이터를 찾을 수 없습니다: {list_id}")

    openschema_data = parse_openschema_json(openschema_path)
    if not openschema_data:
        raise Exception(f"OpenSchema 메타데이터 파싱 실패: {list_id}")

    openschema_id = import_to_database(openschema_data, engine)
    if openschema_id:
        print(f"OpenSchema 메타데이터 저장 완료 (ID: {openschema_id})")
        return openschema_id
    else:
        raise Exception(f"OpenSchema 메타데이터 저장 실패: {list_id}")


def process_dcat(list_id, db_url, result_path: str | Path):
    """DCAT 메타데이터 처리 및 데이터베이스 저장 함수"""
    if not list_id:
        raise Exception(f"처리할 {list_id=}가 필요합니다.")

    # 데이터베이스 연결
    engine = create_engine(db_url)

    # DCAT 메타데이터 다운로드 및 처리
    dcat_path = get_dcat(list_id, result_path)
    if not dcat_path:
        raise Exception(f"DCAT 메타데이터를 찾을 수 없습니다: {list_id}")

    dcat_data = parse_dcat_xml(dcat_path)
    if not dcat_data:
        raise Exception(f"DCAT 메타데이터 파싱 실패: {list_id}")

    dcat_id = import_to_database(dcat_data, engine)
    if dcat_id:
        print(f"DCAT 메타데이터 저장 완료 (ID: {dcat_id})")
        return dcat_id
    else:
        raise Exception(f"DCAT 메타데이터 저장 실패: {list_id}")


def process_metadata(list_id, list_type='standard', db_url=None, result_path: str | Path = config.SAMPLE_DIR,
                     process_type='all'):
    """메타데이터 처리 및 데이터베이스 저장 통합 함수"""
    if not list_id:
        raise Exception(f"처리할 {list_id=}가 필요합니다.")

    results = {}

    # 처리 유형에 따라 필요한 메타데이터만 처리
    if process_type.lower() == 'all' or process_type.lower() == 'openschema':
        openschema_id = process_openschema(list_id, list_type, db_url, result_path)
        results['openschema_id'] = openschema_id

    if process_type.lower() == 'all' or process_type.lower() == 'dcat':
        dcat_id = process_dcat(list_id, db_url, result_path)
        results['dcat_id'] = dcat_id

    return results


# 실행 예제
if __name__ == "__main__":
    # 설정
    db_url = config.DB_URL

    # 경로 설정
    current_path = pathlib.Path(__file__)
    project_root = current_path.parent.parent.parent.parent  # 4단계 상위로 이동
    sample_path = project_root / 'sample'

    list_path = os.path.join(sample_path, 'standard_list.parquet')

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
        results = process_metadata(list_id=list_id_1, list_type="standard", db_url=db_url)
        print(f"처리 결과: {results}")

        # 특정 형식만 처리
        openschema_result = process_metadata(list_id=list_id_2, list_type="standard", db_url=db_url,
                                             result_path=sample_path, process_type='openschema')
        print(f"OpenSchema 처리 결과: {openschema_result}")

        dcat_result = process_metadata(list_id=list_id_3, list_type="standard", db_url=db_url,
                                       result_path=sample_path, process_type='dcat')
        print(f"DCAT 처리 결과: {dcat_result}")

    # 예제 3: 메타데이터 CSV 내보내기
    csv_path = export_to_csv(os.path.join(sample_path, "all_catalog_entries.csv"), db_url)
    print(f"내보낸 CSV 파일 경로: {csv_path}")
