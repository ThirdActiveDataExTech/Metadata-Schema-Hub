import os
from pathlib import Path
from typing import Tuple

import requests

from app.src.datagokr.config import config


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


def download_metadata(list_id: str, list_type: str, save_dir: Path) -> Tuple[str, str]:
    """메타데이터 파일을 다운로드합니다."""
    openschema_path = get_openschema_org(list_id, list_type, save_dir)
    print(f"{openschema_path=} downloaded")

    dcat_path = get_dcat(list_id, save_dir)
    print(f"{dcat_path=} downloaded")

    return openschema_path, dcat_path


if __name__ == "__main__":
    # 샘플 값 사용 방법: https://www.data.go.kr/data/{LIST_ID}/{LIST_TYPE}.do
    # 예시: https://www.data.go.kr/data/15141808/openapi.do
    sample_list_id = "15129441"
    sample_list_type = "standard"  # "standard", "file", "openapi"

    openschema_path = get_openschema_org(sample_list_id, sample_list_type)
    print(f"{openschema_path=} downloaded")

    dcat_path = get_dcat(sample_list_id)
    print(f"{dcat_path=} downloaded")
