import json
import os
import pathlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict

import pandas as pd

from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.catalog_entry.service import CatalogEntryService
from app.src.datagokr.config import config
from app.src.util.util import sample_data, to_str_list


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
    readers: Dict[str, Callable] = {".parquet": pd.read_parquet, ".csv": pd.read_csv}

    # 파일 경로에서 확장자 추출
    ext = Path(data_path).suffix.lower()

    # 지원되는 확장자인지 확인 후 해당 리더 함수 실행
    if ext in readers:
        return readers[ext](data_path)

    # 지원되지 않는 확장자일 경우 오류 발생
    supported_extensions = ", ".join(readers.keys())
    raise ValueError(f"지원되지 않는 파일 형식: {data_path}, 지원 확장자: {supported_extensions}")


def transform_data(list_path: str | Path, save_dir: str | Path):
    """데이터를 DCAT 구조에 맞게 변환합니다.

    Args:
        list_path (str | Path): 리스트 데이터 파일 경로
        save_dir (str | Path): 저장 디렉토리

    Returns:
        list: DCAT 형식으로 변환된 카탈로그 항목 목록
    """
    # 파일 읽기
    list_df = data_reader(list_path)

    # 저장 경로 확인 및 생성
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    catalog_entries = []

    for _, row in list_df.iterrows():
        # 필수 ID 확인
        list_id = str(row["list_id"])
        if not list_id:
            raise ValueError(f"유효하지 않은 list_id: {list_id}")

        list_type = get_dataset_type(row)

        # Landing page URL 생성
        landing_page = f"{config.LANDING_URL_PREFIX}{list_id}/{list_type}.do"

        # DCAT 항목 생성
        entry = create_catalog_entry(row, landing_page)
        catalog_entries.append(entry)

    return catalog_entries


def get_dataset_type(dataset_row: pd.Series) -> str:
    """데이터셋의 유형을 결정합니다.

    Args:
        dataset_row: 데이터셋 정보가 담긴 Pandas Series

    Returns:
        str: 데이터셋 유형 문자열
    """
    list_type = str(dataset_row["list_type"])
    if not list_type:
        list_type = config.LANDING_URL_SUFFIX["standard"]
    return list_type


def create_catalog_entry(dataset_row: pd.Series, landing_page: str) -> Dict[str, Any]:
    """데이터셋 정보로부터 DCAT 형식의 카탈로그 항목을 생성합니다.

    Args:
        dataset_row: 데이터셋 정보가 담긴 Pandas Series
        landing_page: 데이터셋 랜딩 페이지 URL

    Returns:
        Dict[str, Any]: DCAT 스키마에 맞는 카탈로그 항목
    """
    return {
        # DCAT 필수 필드
        "title": dataset_row["title"],
        "description": dataset_row["desc"],
        "issued": parse_date(dataset_row["created_at"]),
        "modified": parse_date(dataset_row["updated_dt"]),
        # dataset 필드
        "identifier": dataset_row["id"],
        "publisher": json.dumps({"name": dataset_row["org_nm"], "code": dataset_row["org_cd"]}),
        "keyword": to_str_list(dataset_row["keywords"]),
        "landing_page": landing_page,
        "theme": [dataset_row["category_nm"]],
        # distribution 필드
        "access_url": landing_page,
        # 원본 메타데이터 저장
        "raw_metadata": json.dumps({k: str(v) if pd.notna(v) else None for k, v in dataset_row.items()}),
    }


def parse_date(date_str):
    """날짜 문자열을 파싱하여 YYYY-MM-DD 형식으로 반환"""
    if pd.isna(date_str):
        return None

    try:
        # 여러 형식의 날짜 처리
        for fmt in ["%Y-%m-%d", "%Y%m%d"]:
            try:
                date_obj = datetime.strptime(str(date_str)[:10], fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception as e:
        print(f"날짜 파싱 오류: {date_str}, {e}")

    return None


if __name__ == "__main__":
    current_path = pathlib.Path(__file__)
    project_root = current_path.parent.parent.parent.parent  # 4단계 상위로 이동
    sample_path = project_root / "sample"

    raw_list_path = os.path.join(sample_path, "standard_list.parquet")

    # 임시 디렉토리 생성하여 작업
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. 데이터 샘플링 및 임시 파일 저장
        list_sample_path = sample_data(raw_list_path, temp_dir)

        # 2. 데이터 변환
        processed_data = transform_data(list_sample_path, sample_path)

        # 3. 데이터 삽입
        repository = CatalogEntryRepository()
        service = CatalogEntryService(repository)
        # service.insert_data(processed_data)
