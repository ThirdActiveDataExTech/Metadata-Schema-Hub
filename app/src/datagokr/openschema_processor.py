import json
import os
from typing import List, Any

from app.src.datagokr.util import parse_date, extract_keywords


def parse_openschema_json(file_path):
    """OpenSchema.org JSON 파일 파싱, 다중 언어 지원"""
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path=} not found.")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 다국어 필드 처리 함수
        def extract_multilang_field(data, field_name, lang_preference="kr"):
            value = data.get(field_name, '')

            # 단일 값인 경우
            if not isinstance(value, dict) and not isinstance(value, list):
                return value

            # 딕셔너리에 언어 키가 있는 경우
            if isinstance(value, dict):
                # 선호 언어가 있으면 반환
                if lang_preference in value:
                    return value[lang_preference]
                # 한국어 키가 있으면 반환
                elif "kr" in value:
                    return value["kr"]
                elif "ko" in value:
                    return value["ko"]
                # 영어 키가 있으면 반환
                elif "en" in value:
                    return value["en"]
                # 첫 번째 값 반환
                else:
                    for key, val in value.items():
                        if key not in ["@type", "@context"]:  # 메타데이터 키 제외
                            return val

            # 리스트인 경우 (예: [{"@language": "kr", "@value": "한글값"}, {"@language": "en", "@value": "English"}])
            if isinstance(value, list):
                # 언어 선호도에 따라 반환
                lang_items = {item.get("@language", ""): item.get("@value", "")
                              for item in value if isinstance(item, dict)}

                if lang_preference in lang_items:
                    return lang_items[lang_preference]
                elif "kr" in lang_items:
                    return lang_items["kr"]
                elif "ko" in lang_items:
                    return lang_items["ko"]
                elif "en" in lang_items:
                    return lang_items["en"]
                elif lang_items:
                    return next(iter(lang_items.values()))
                elif value:
                    return value[0] if isinstance(value[0], str) else str(value[0])

            return str(value) if value else ''

        # OpenSchema.org 형식에서 catalog_entry 테이블에 맞게 매핑
        result = {
            'title': extract_multilang_field(data, 'name'),
            'description': extract_multilang_field(data, 'description'),
            'issued': parse_date(data.get('dateCreated')),
            'modified': parse_date(data.get('dateModified')),
            'identifier': data.get('identifier', ''),
            'publisher': extract_publisher(data),
            'keyword': extract_keywords(data.get('keywords', '')),
            'landing_page': data.get('url', ''),
            'theme': extract_themes(data),
            'access_url': data.get('url', ''),
            'raw_metadata': data
        }

        return result
    except Exception as e:
        raise Exception(f"OpenSchema.org JSON 파싱 오류: {e}")


def extract_publisher(data):
    """OpenSchema.org JSON에서 publisher 정보 추출"""
    publisher = data.get('publisher', {})
    if isinstance(publisher, dict):
        return json.dumps(publisher, ensure_ascii=False)
    return json.dumps({'name': str(publisher) if publisher else ''}, ensure_ascii=False)


def extract_media_type(data):
    """OpenSchema.org JSON에서 media_type 정보 추출"""
    # 실제 데이터 구조에 맞게 조정 필요
    distribution = data.get('distribution', [])
    if distribution and isinstance(distribution, list) and len(distribution) > 0:
        return distribution[0].get('encodingFormat', '')
    return ''


def extract_package_format(data):
    """OpenSchema.org JSON에서 package_format 정보 추출"""
    # 실제 데이터 구조에 맞게 조정 필요
    distribution = data.get('distribution', [])
    if distribution and isinstance(distribution, list) and len(distribution) > 0:
        return distribution[0].get('contentUrl', '').split('.')[-1] if distribution[0].get('contentUrl') else ''
    return ''


def extract_format(data):
    """OpenSchema.org JSON에서 format 정보 추출"""
    # 실제 데이터 구조에 맞게 조정 필요
    return extract_media_type(data) or extract_package_format(data)


def extract_byte_size(data):
    """OpenSchema.org JSON에서 byte_size 정보 추출"""
    distribution = data.get('distribution', [])
    if distribution and isinstance(distribution, list) and len(distribution) > 0:
        return distribution[0].get('contentSize', '')
    return ''


def extract_download_url(data):
    """OpenSchema.org JSON에서 download_url 정보 추출"""
    distribution = data.get('distribution', [])
    if distribution and isinstance(distribution, list) and len(distribution) > 0:
        return distribution[0].get('contentUrl', '')
    return ''


def extract_themes(data) -> List[Any]:
    """OpenSchema.org JSON에서 theme 정보 추출"""
    about = data.get('about', [])
    if isinstance(about, list):
        return [item.get('name', '') for item in about if item.get('name')]
    return []
