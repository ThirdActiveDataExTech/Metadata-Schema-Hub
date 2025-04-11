import datetime
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd
import requests
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app.schemas.catalog_entry import CatalogEntry
from app.src.datagokr.config import config
from app.src.datagokr.util import ensure_directory


def get_openschema_org(list_id, list_type: str = 'standard', save_dir: str | Path = config.SAMPLE_DIR) -> str:
    """OpenSchema.org 메타데이터를 다운로드하고 저장.

    Args:
        list_id (str): 데이터셋 ID
        list_type (str): 데이터 타입 (standard, open, file 등)
        save_dir (str): 저장할 디렉토리 경로

    Returns:
        str: 저장된 파일 경로 또는 None (실패 시)
    """
    if not list_id:
        raise Exception(f"{list_id=} is required.")

    # list_type을 적절한 접미사로 변환
    suffix = config.LANDING_URL_SUFFIX.get(list_type.lower() if list_type else 'standard', 'standard')

    # URL 생성
    url = f"{config.OPENSCHEMA_URL_PREFIX}{list_id}/{suffix}.json"

    try:
        # 요청 전송 및 응답 확인
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # 4XX, 5XX 오류 확인

        # 저장할 파일 경로 생성
        filename = f"openschema_{list_id}.json"
        file_path = os.path.join(save_dir, filename)

        # 파일 저장
        with open(file_path, 'wb') as f:
            f.write(response.content)

        print(f"OpenSchema 메타데이터 저장 완료: {file_path}")
        return file_path

    except requests.exceptions.RequestException as e:
        raise Exception(f"OpenSchema 메타데이터 다운로드 실패 ({url=}): {e}")


def get_dcat(list_id, save_dir: str | Path = config.SAMPLE_DIR) -> str:
    """DCAT 메타데이터를 다운로드하고 저장.

    Args:
        list_id (str): 데이터셋 ID
        save_dir (str): 저장할 디렉토리 경로

    Returns:
        str: 저장된 파일 경로 또는 None (실패 시)
    """
    if not list_id:
        raise Exception(f"{list_id=} is required.")

    # URL 생성
    url = f"{config.DCAT_URL_PREFIX}{list_id}"

    try:
        # 요청 전송 및 응답 확인
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # 4XX, 5XX 오류 확인

        # 저장할 파일 경로 생성
        filename = f"dcat_{list_id}.rdf"  # 또는 .ttl, .rdf 등 실제 형식에 맞게 조정 필요
        file_path = os.path.join(save_dir, filename)

        # 파일 저장
        with open(file_path, 'wb') as f:
            f.write(response.content)

        print(f"DCAT 메타데이터 저장 완료: {file_path}")
        return file_path

    except requests.exceptions.RequestException as e:
        raise Exception(f"DCAT 메타데이터 다운로드 실패 ({url=}): {e}")


def export_to_csv(output_path: str | Path | None = None, db_url: str = None, limit: int = None):
    """데이터베이스의 catalog_entry 테이블 전체를 CSV로 내보내기"""
    if not output_path:
        output_path = os.path.join(config.SAMPLE_DIR, "catalog_entries.csv")

    # 파일이 저장될 디렉토리 확인 및 생성
    output_dir = os.path.dirname(output_path)
    ensure_directory(output_dir)

    # 데이터베이스 연결
    engine = create_engine(db_url)

    try:
        with Session(engine) as session:
            # 모든 레코드 조회 쿼리 작성 (필요시 limit 추가)
            statement = select(CatalogEntry)
            if limit:
                statement = statement.limit(limit)

            # 쿼리 실행
            results = session.exec(statement).all()

            if not results:
                print("내보낼 데이터가 없습니다.")
                return None

            # 결과를 딕셔너리 리스트로 변환
            data_list = []
            for result in results:
                # SQLModel 0.0.14부터 dict() 대신 model_dump() 사용
                data = result.model_dump()

                # 날짜 필드 문자열 변환
                if 'issued' in data and data['issued']:
                    data['issued'] = str(data['issued'])

                if 'modified' in data and data['modified']:
                    data['modified'] = str(data['modified'])

                if 'ingested_at' in data and data['ingested_at']:
                    data['ingested_at'] = str(data['ingested_at'])

                if 'updated_at' in data and data['updated_at']:
                    data['updated_at'] = str(data['updated_at'])

                # JSONB 필드는 문자열로 변환하여 CSV에 저장
                if 'publisher' in data and isinstance(data['publisher'], dict):
                    data['publisher'] = json.dumps(data['publisher'], ensure_ascii=False)

                if 'raw_metadata' in data:
                    # raw_metadata는 너무 크고 복잡하므로 CSV에서 제외
                    data.pop('raw_metadata', None)

                # 배열 타입 필드 (keyword, theme)도 문자열로 변환
                if 'keyword' in data and isinstance(data['keyword'], list):
                    data['keyword'] = ','.join(data['keyword']) if data['keyword'] else ''

                if 'theme' in data and isinstance(data['theme'], list):
                    data['theme'] = ','.join(data['theme']) if data['theme'] else ''

                data_list.append(data)

            # pandas DataFrame으로 변환
            df = pd.DataFrame(data_list)

            # CSV 파일로 저장
            df.to_csv(output_path, index=False, encoding='utf-8-sig')  # BOM 포함 UTF-8로 저장

            print(f"CSV 내보내기 완료: {output_path} (총 {len(data_list)}개 레코드)")
            return output_path

    except Exception as e:
        import traceback
        traceback.print_exc()  # 상세 오류 메시지 출력
        raise Exception(f"데이터베이스 CSV 내보내기 오류: {e}")


def download_metadata(list_id: str, list_type: str, save_dir: Path) -> Tuple[str, str]:
    """메타데이터 파일을 다운로드합니다."""
    openschema_path = get_openschema_org(list_id, list_type, save_dir)
    print(f"{openschema_path=} downloaded")

    dcat_path = get_dcat(list_id, save_dir)
    print(f"{dcat_path=} downloaded")

    return openschema_path, dcat_path


def log_queries(conn, cursor, statement, params, context, executemany):
    """쿼리 로깅 함수."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"query_dump_{timestamp}.sql"

    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"-- Executed at: {datetime.now()}\n\n")

        # 실제 값으로 대체된 쿼리 생성
        if params:
            try:
                # 배치 쿼리인 경우 (params가 리스트인 경우)
                if isinstance(params, list):
                    for i, param_dict in enumerate(params):
                        # %(name)s 형식의 파라미터를 실제 값으로 대체
                        actual_query = statement
                        for key, value in param_dict.items():
                            # 값 타입에 따른 처리
                            if value is None:
                                replacement = "NULL"
                            elif isinstance(value, str):
                                # JSON 문자열인 경우 UTF-8로 디코딩
                                if key == 'raw_metadata' or key == 'publisher':
                                    try:
                                        json_obj = json.loads(value)
                                        pretty_json = json.dumps(json_obj, ensure_ascii=False)
                                        replacement = f"'{pretty_json}'"
                                    except:
                                        replacement = f"'{value}'"
                                else:
                                    replacement = f"'{value}'"
                            elif isinstance(value, (list, dict)):
                                # 리스트나 딕셔너리는 JSON으로 변환
                                replacement = f"'{json.dumps(value, ensure_ascii=False)}'"
                            elif isinstance(value, (int, float)):
                                replacement = str(value)
                            elif isinstance(value, datetime.date):
                                replacement = f"'{value}'"
                            else:
                                replacement = f"'{value}'"

                            # 파라미터 이름 패턴 (%(name)s)에 맞춰 대체
                            param_pattern = f'%\\({key}\\)s'
                            actual_query = re.sub(param_pattern, replacement, actual_query)

                        # 쿼리 끝에 세미콜론 추가
                        if not actual_query.strip().endswith(';'):
                            actual_query = actual_query.strip() + ';'

                        f.write(f"{actual_query}\n\n")
                # 단일 쿼리인 경우
                elif isinstance(params, dict):
                    actual_query = statement
                    for key, value in params.items():
                        # 값 타입에 따른 처리
                        if value is None:
                            replacement = "NULL"
                        elif isinstance(value, str):
                            if key == 'raw_metadata' or key == 'publisher':
                                try:
                                    json_obj = json.loads(value)
                                    pretty_json = json.dumps(json_obj, ensure_ascii=False)
                                    replacement = f"'{pretty_json}'"
                                except:
                                    replacement = f"'{value}'"
                            else:
                                replacement = f"'{value}'"
                        elif isinstance(value, (list, dict)):
                            replacement = f"'{json.dumps(value, ensure_ascii=False)}'"
                        elif isinstance(value, (int, float)):
                            replacement = str(value)
                        elif isinstance(value, datetime.date):
                            replacement = f"'{value}'"
                        else:
                            replacement = f"'{value}'"

                        param_pattern = f'%\\({key}\\)s'
                        actual_query = re.sub(param_pattern, replacement, actual_query)

                    # 쿼리 끝에 세미콜론 추가
                    if not actual_query.strip().endswith(';'):
                        actual_query = actual_query.strip() + ';'

                    f.write(f"{actual_query}\n\n")
            except Exception as e:
                f.write(f"-- Error generating actual query: {str(e)}\n")

        f.write("-- " + "-" * 50 + "\n\n")


if __name__ == "__main__":
    # 샘플 값 사용 방법: https://www.data.go.kr/data/{LIST_ID}/{LIST_TYPE}.do
    # 예시: https://www.data.go.kr/data/15141808/openapi.do
    sample_list_id = "15129441"
    sample_list_type = "standard"  # "standard", "file", "openapi"

    openschema_path = get_openschema_org(sample_list_id, sample_list_type)
    print(f"{openschema_path=} downloaded")

    dcat_path = get_dcat(sample_list_id)
    print(f"{dcat_path=} downloaded")
