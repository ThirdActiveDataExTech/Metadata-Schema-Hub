import json
import os
from typing import Dict, Any, List

from app.src.datagokr.util import parse_date, extract_keywords


def parse_schema_org_json(file_path) -> Dict[str, Any]:
    """Schema.org JSON 파일 파싱, 다중 언어 지원"""
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path=} not found.")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        # Schema.org 형식에서 catalog_entry 테이블에 맞게 매핑
        result: Dict[str, Any] = {
            "title": extract_multilang_field(data["name"]),
            "description": extract_multilang_field(data["description"]),
            "issued": parse_date(data.get("datePublished", "")),
            "modified": parse_date(data.get("dateModified", "")),
            "identifier": data.get("identifier", ""),
            "publisher": extract_publisher(data.get("creator", "")),
            "keyword": extract_keywords(data.get("keywords", "")),
            "landing_page": data.get("url", ""),
            "theme": extract_theme(data.get("additionalType", "")),
            "access_url": data.get("url", ""),  # TODO: access_url schema.org에 없음
            "raw_metadata": data,
        }

        return result
    except Exception as e:
        raise Exception(f"Schema.org JSON 파싱 오류: {e}")


def extract_multilang_field(field: Any, lang_preference: str = "kr") -> str:
    """언어값 추출 함수

    문자열과 리스트만 처리하는 언어값 추출 함수
    - 문자열: 그대로 반환
    - 리스트: 언어 우선순위 적용 (kr > en > 기타)

    Args:
        field (Any): 처리할 필드 값
        lang_preference (str, optional): 선호하는 언어 코드. 기본값 "kr"

    Returns:
        str: 추출된 언어값
    """
    # 문자열인 경우 바로 반환
    if isinstance(field, str):
        return field

    # 리스트 처리
    if isinstance(field, list) and field:
        # language/value 형식의 객체 리스트 처리
        lang_values = {}
        for item in field:
            if isinstance(item, dict):
                lang = item.get("@language", "")
                val = item.get("@value", "")
                if lang and val:
                    lang_values[lang] = val

        # 언어 우선순위 적용
        if lang_preference in lang_values:
            return lang_values[lang_preference]
        elif "kr" in lang_values:
            return lang_values["kr"]
        elif "en" in lang_values:
            return lang_values["en"]
        elif lang_values:
            return next(iter(lang_values.values()))

    # 기타 타입은 문자열 변환 시도
    try:
        return str(field) if field is not None else ""
    except:
        return ""


def extract_publisher(publisher: Any) -> Dict[str, Any]:
    """Schema.org JSON에서 publisher 정보 추출"""
    if not isinstance(publisher, dict):
        publisher = {"name": str(publisher) if publisher else ""}
    return publisher

def extract_theme(field: Any) -> List[Any]:
    """Schema.org JSON에서 theme 정보 추출"""
    if not isinstance(field, list):
        return [field]
    return [str(item) if not isinstance(item, str) else item for item in field]
