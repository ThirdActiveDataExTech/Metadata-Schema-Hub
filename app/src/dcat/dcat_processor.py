import os
from typing import Any, Dict, List

import xmltodict

from app.src.util.util import parse_date, to_str_list


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
            'title': extract_multilang_field(dataset.get("dct:title", "")),
            'description': extract_multilang_field(dataset.get("dct:description", "")),
            'issued': parse_date(dataset.get("dct:issued", "")),
            'modified': parse_date(find_modified(dataset)),
            'identifier': dataset.get("dct:identifier", ""),
            'publisher': find_publisher(dataset),
            'keyword': to_str_list(extract_multilang_field(dataset.get("dcat:keyword", ""))),
            'landing_page': find_landing_page(dataset),
            'theme': to_str_list(dataset.get("dcat:theme", "")),
            'access_url': distribution.get("dcat:accessURL", ""),
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


def extract_multilang_field(values: List[Dict[str, Any]], lang_preference: str = "kr") -> str:
    """다국어 필드에서 우선순위 언어값 추출."""
    lang_formats = ["kr", "en"]
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Not Acceptable Format")
        # 언어 속성 확인
        lang = item.get("@xml:lang", "")
        text = item.get("#text", "")

        # 선호 언어 찾았으면 바로 반환
        if lang == lang_preference:
            return text

        for lang_format in lang_formats:
            if lang == lang_format:
                return text

    return values[0]["#text"]  # 선호 언어 없을 경우 첫번쨰로 등장하는 언어 값 리턴


def find_modified(dataset: Dict[str, Any]) -> str:
    """XML에서 modified 정보 추출"""
    modified = dataset.get("dct:modified", "")

    if isinstance(modified, dict):
        return modified.get("#text", "")

    return str(modified)


def find_publisher(dataset: Dict[str, Any]) -> str:
    """XML에서 publisher 정보 추출"""
    publisher = dataset.get("dct:publisher", {})
    org = publisher.get("foaf:Organization", {})
    name = org.get("foaf:name", "")

    return name


def find_landing_page(dataset: Dict[str, Any]) -> str:
    """Find landing_page."""
    landing_page = dataset.get("dcat:landingPage", "")
    if isinstance(landing_page, dict):
        return landing_page.get("@rdf:resource", "")

    return str(landing_page)
