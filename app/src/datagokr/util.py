import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd


def ensure_directory(directory):
    """디렉토리가 존재하는지 확인하고, 없으면 생성"""
    Path(directory).mkdir(parents=True, exist_ok=True)
    return directory


def clean_json_string(json_str):
    """문자열로 저장된 JSON 데이터를 파싱하여 이스케이프된 따옴표 제거"""
    if not json_str or not isinstance(json_str, str):
        return json_str

    try:
        # 이미 파이썬 객체인 경우 그대로 반환
        if isinstance(json_str, dict):
            return json_str

        # JSON 문자열을 파이썬 객체로 변환
        parsed_data = json.loads(json_str)
        return parsed_data
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 원본 반환
        return json_str


def parse_date(date_str) -> date | None:
    """날짜 문자열을 파싱하여 YYYY-MM-DD 형식으로 변환"""
    if not date_str:
        return None

    try:
        # 다양한 날짜 형식 처리
        for fmt in ['%Y-%m-%d', '%Y%m%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
            try:
                date_obj = datetime.strptime(str(date_str)[:19], fmt)
                return date_obj.date()
            except ValueError:
                continue
    except Exception as e:
        print(f"날짜 파싱 오류: {date_str}, {e}")

    return None


def extract_keywords(keyword_str):
    """키워드 문자열을 리스트로 변환"""
    if not keyword_str:
        return []

    if isinstance(keyword_str, list):
        return keyword_str

    # 다양한 구분자 처리
    for sep in [',', ';', '/', '|']:
        if sep in keyword_str:
            return [k.strip() for k in keyword_str.split(sep) if k.strip()]

    # 구분자가 없으면 단일 키워드로 처리
    return [keyword_str.strip()]


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
