import os
from typing import Dict, Any

import xmltodict

from app.src.datagokr.util import parse_date


def parse_dcat_xml(file_path) -> Dict[str, Any]:
    """DCAT XML 파일 파싱, 다중 언어 지원"""
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path=} not found.")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_data = f.read()

        # XML을 딕셔너리로 변환
        data_dict = xmltodict.parse(xml_data)

        # 필요한 네임스페이스 처리
        dataset = find_dataset(data_dict)
        if not dataset:
            raise Exception(f"DCAT XML에서 데이터셋을 찾을 수 없습니다: {file_path}")

        # catalog_entry 테이블에 맞게 매핑
        distribution = find_distribution(dataset)

        result: Dict[str, Any] = {
            'title': extract_xml_value(dataset, 'dct:title', "kr"),
            'description': extract_xml_value(dataset, 'dct:description', "kr"),
            'issued': parse_date(extract_xml_value(dataset, 'dct:issued')),
            'modified': parse_date(extract_xml_value(dataset, 'dct:modified')),
            'identifier': extract_xml_value(dataset, 'dct:identifier'),
            'publisher': extract_xml_publisher(dataset),
            'keyword': extract_xml_keywords(dataset),
            'landing_page': extract_xml_value(dataset, 'dcat:landingPage'),
            'theme': extract_xml_themes(dataset),
            'access_url': extract_xml_value(distribution, 'dcat:accessURL') if distribution else '',
            'raw_metadata': data_dict
        }

        return result
    except Exception as e:
        raise Exception(f"DCAT XML 파싱 오류: {e}")


def find_dataset(data_dict):
    """XML 딕셔너리에서 데이터셋 요소 찾기"""
    # 일반적인 구조 예상 (실제 XML 구조에 맞게 조정 필요)
    catalog = data_dict.get('rdf:RDF', {}).get('dcat:Catalog', {})
    dataset = catalog.get('dcat:dataset', {}).get('dcat:Dataset', {})
    return dataset


def find_distribution(dataset):
    """데이터셋에서 배포판 요소 찾기"""
    distribution = dataset.get('dcat:distribution', {}).get('dcat:Distribution', {})
    return distribution


def extract_xml_value(element, key, lang_preference="kr"):
    """XML 요소에서 특정 키의 값 추출, 다중 언어 지원"""
    if not element or not key:
        return ''

    value = element.get(key, '')

    # 값이 없는 경우
    if not value:
        return ''

    # 단일 문자열인 경우
    if isinstance(value, str):
        return value

    # dict이고 #text가 있는 경우 (단일 언어)
    if isinstance(value, dict) and '#text' in value:
        return value['#text']

    # dict이고 xml:lang 속성이 있는 경우
    if isinstance(value, dict) and '@xml:lang' in value:
        return value.get('#text', '')

    # 리스트인 경우 (다중 언어)
    if isinstance(value, list):
        # 언어 선호도에 따라 정렬
        lang_priority = {"kr": 3, "ko": 2, "en": 1}

        # 기본값 저장
        default_text = ''

        # 선호 언어 검색
        for item in value:
            if isinstance(item, dict):
                # 언어 속성 확인
                lang = item.get('@xml:lang', '')
                text = item.get('#text', '')

                # 선호 언어 찾았으면 바로 반환
                if lang == lang_preference:
                    return text

                # 첫 항목이나 한국어 관련 항목을 기본값으로 설정
                if not default_text or lang in lang_priority:
                    if not default_text or (lang in lang_priority and
                                            lang_priority.get(lang, 0) > lang_priority.get(default_lang, 0)):
                        default_text = text
                        default_lang = lang
            elif not default_text:
                # 단순 문자열인 경우 첫 항목을 기본값으로
                default_text = str(item)

        return default_text

    # 그 외 경우는 문자열로 변환
    return str(value) if value else ''


def extract_xml_publisher(dataset):
    """XML에서 publisher 정보 추출"""
    publisher = dataset.get('dct:publisher', {})
    if isinstance(publisher, dict):
        org = publisher.get('foaf:Organization', {})

        # 문자열 값 추출
        name = extract_xml_value(org, 'foaf:name')
        mbox = extract_xml_value(org, 'foaf:mbox')

        # 직접 딕셔너리 생성하여 JSON 문자열화 단계 건너뛰기
        return {
            'name': name,
            'mbox': mbox
        }

    # 단순 문자열인 경우
    return {'name': str(publisher) if publisher else ''}


def extract_xml_keywords(dataset):
    """XML에서 키워드 추출"""
    keywords = dataset.get('dcat:keyword', [])
    if not keywords:
        return []

    if isinstance(keywords, str):
        return [keywords]

    if isinstance(keywords, list):
        return [k['#text'] if isinstance(k, dict) and '#text' in k else str(k) for k in keywords]

    if isinstance(keywords, dict) and '#text' in keywords:
        return [keywords['#text']]

    return [str(keywords)]


def extract_xml_themes(dataset):
    """XML에서 테마 추출"""
    themes = dataset.get('dcat:theme', [])
    if not themes:
        return []

    if isinstance(themes, str):
        return [themes]

    if isinstance(themes, list):
        return [t['#text'] if isinstance(t, dict) and '#text' in t else str(t) for t in themes]

    if isinstance(themes, dict) and '#text' in themes:
        return [themes['#text']]

    return [str(themes)]
