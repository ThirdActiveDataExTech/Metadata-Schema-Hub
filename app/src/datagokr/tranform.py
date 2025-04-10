import json
import os
import pathlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Callable

import pandas as pd
from sqlalchemy import create_engine, text

from app.src.datagokr.config import config
from extractor import get_openschema_org, get_dcat


def sample_data(df_path: str, output_dir: str | Path, sample_size: int = 5) -> str:
    """데이터프레임에서 샘플링을 수행하고 파일로 저장합니다.

    입력 파일의 이름에 '_sample' 접미사를 추가하여 샘플 파일을 저장합니다.

    Args:
        df_path (str): 원본 데이터 파일 경로
        output_dir (str | Path): 샘플 데이터를 저장할 디렉토리
        sample_size (int, optional): 샘플링할 데이터 크기. 기본값은 5.

    Returns:
        str: 저장된 샘플 파일의 경로
    """
    # Parquet 파일 읽기
    df = pd.read_parquet(df_path)

    # 샘플링 수행
    df_sample = df.head(sample_size)

    # 저장 경로 확인 및 생성
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 원본 파일 이름 가져오기
    original_filename = Path(df_path).stem

    # 샘플 데이터 저장 - 원본 파일명_sample.parquet 형식으로 저장
    df_sample_path = output_dir / f"{original_filename}_sample.parquet"

    df_sample.to_parquet(df_sample_path)

    return str(df_sample_path)


def data_reader(data_path: str | Path) -> pd.DataFrame:
    """파일 확장자에 따라 적절한 판다스 리더 함수를 사용하여 데이터를 읽어옵니다.

    Args:
        data_path: 데이터 파일 경로

    Returns:
        pd.DataFrame: 읽어온 데이터프레임

    Raises:
        ValueError: 지원되지 않는 파일 형식일 경우
    """
    # 확장자별 리더 함수 매핑
    readers: Dict[str, Callable] = {
        '.parquet': pd.read_parquet,
        '.csv': pd.read_csv
    }

    # 파일 경로에서 확장자 추출
    ext = Path(data_path).suffix.lower()

    # 지원되는 확장자인지 확인 후 해당 리더 함수 실행
    if ext in readers:
        return readers[ext](data_path)

    # 지원되지 않는 확장자일 경우 오류 발생
    supported_extensions = ', '.join(readers.keys())
    raise ValueError(f"지원되지 않는 파일 형식: {data_path}, 지원 확장자: {supported_extensions}")


def transform_data(list_path: str | Path, save_dir: str | Path):
    """데이터를 DCAT 구조에 맞게 변환합니다.

    Args:
        list_path (str | Path): 리스트 데이터 파일 경로
        save_dir (str | Path): 저장 디렉토리

    Returns:
        list: 변환된 데이터 목록
    """
    # 파일 읽기
    list_df = data_reader(list_path)

    # 저장 경로 확인 및 생성
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    merged_data = []

    for _, list_row in list_df.iterrows():
        # OpenSchema 및 DCAT 메타데이터 다운로드
        list_id = str(list_row['list_id'])
        if len(list_id) <= 0:
            raise Exception(f"{list_id=} is na.")

        list_type = str(list_row['list_type'])
        if len(list_type) <= 0:
            list_type = config.LANDING_URL_SUFFIX.get("standard")

        openschema_path = get_openschema_org(list_id, list_type, save_dir)
        print(f"{openschema_path=} downloaded")

        dcat_path = get_dcat(list_id, save_dir)
        print(f"{dcat_path=} downloaded")

        landing_page: str = f"{config.LANDING_URL_PREFIX}{list_id}/{list_type}.do"

        # DCAT 구조에 맞게 데이터 변환
        # TODO: Mapping table, 가독성, 변경용이성 필요
        entry = {
            # DCAT 필수 필드
            'title': list_row['title'],
            'description': list_row['desc'],
            'issued': parse_date(list_row['created_at']),
            'modified': parse_date(list_row['updated_dt']),

            # dataset 필드
            'identifier': list_row['id'],
            'publisher': json.dumps({
                'name': list_row['org_nm'],
                'code': list_row['org_cd']
            }),
            'keyword': parse_keywords(list_row['keywords']),
            'landing_page': landing_page,
            'theme': [list_row['category_nm']],
            # 'version': None,  # 버전 정보가 없음

            # distribution 필드
            'access_url': landing_page,
            # 'byte_size': None,  # 크기 정보가 없음
            # 'download_url': None,  # 다운로드 URL 정보가 없음
            # 'media_type': None,  # MIME 타입 정보가 없음
            # 'package_format': None,
            # 'format': None,

            # 원본 메타데이터 저장
            'raw_metadata': json.dumps({k: str(v) if pd.notna(v) else None for k, v in list_row.items()})
        }

        merged_data.append(entry)

    return merged_data


def insert_data(merged_data, host: str):
    """변환된 데이터를 데이터베이스에 삽입합니다.

    Args:
        merged_data (list): 변환된 데이터 목록
        host (str): 데이터베이스 연결 문자열
    """
    # PostgreSQL에 연결
    engine = create_engine(host)

    # 데이터 삽입
    queries = []

    with engine.connect() as conn:
        for entry in merged_data:
            # SQL 구문 작성
            insert_stmt = text("""
                INSERT INTO catalog_entry (
                    title, description, issued, modified, identifier, publisher, 
                    keyword, landing_page, theme, access_url, raw_metadata
                ) VALUES (
                    :title, :description, :issued, :modified, :identifier, :publisher,
                    :keyword, :landing_page, :theme, :access_url, :raw_metadata
                )
            """)

            queries.append(insert_stmt)

            # 배열 타입 처리
            entry_copy = entry.copy()
            if entry_copy['keyword'] is not None:
                entry_copy['keyword'] = list(filter(None, entry_copy['keyword']))
            if entry_copy['theme'] is not None:
                entry_copy['theme'] = list(filter(None, entry_copy['theme']))

            # 삽입 실행
            conn.execute(insert_stmt, entry_copy)

        conn.commit()

    print(queries)

    print(f"총 {len(merged_data)}개의 데이터가 catalog_entry 테이블에 삽입되었습니다.")


def parse_date(date_str):
    """날짜 문자열을 파싱하여 YYYY-MM-DD 형식으로 반환"""
    if pd.isna(date_str):
        return None

    try:
        # 여러 형식의 날짜 처리
        for fmt in ['%Y-%m-%d', '%Y%m%d']:
            try:
                date_obj = datetime.strptime(str(date_str)[:10], fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
    except Exception as e:
        print(f"날짜 파싱 오류: {date_str}, {e}")

    return None


def parse_keywords(keyword_str):
    """키워드 문자열을 리스트로 변환"""
    if pd.isna(keyword_str) or not keyword_str:
        return []

    # 다양한 구분자 처리
    for sep in [',', ';', '/', '|']:
        if sep in keyword_str:
            return [k.strip() for k in keyword_str.split(sep)]

    # 구분자가 없으면 단일 키워드로 처리
    return [keyword_str.strip()]


if __name__ == "__main__":
    current_path = pathlib.Path(__file__)
    project_root = current_path.parent.parent.parent.parent  # 4단계 상위로 이동
    sample_path = project_root / 'sample'

    raw_list_path = os.path.join(sample_path, 'standard_list.parquet')

    psql_host = config.DB_URL

    # 임시 디렉토리 생성하여 작업
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. 데이터 샘플링 및 임시 파일 저장
        list_sample_path = sample_data(raw_list_path, temp_dir)

        # 2. 데이터 변환
        merged_data = transform_data(list_sample_path, sample_path)

        # 3. 데이터 삽입
        insert_data(merged_data, psql_host)
