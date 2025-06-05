from typing import List, Dict

from lxml import etree

from app.schemas.metadata_entry import MetadataBase
from app.src.metadata_entry.namespace_handler import NamespaceHandler


class LxmlConverter:
    """lxml 기반 고성능 XML 변환기"""

    def __init__(self):
        """RDF 변환기 초기화."""
        self.ns_handler = NamespaceHandler()

    def _build_path(self, element) -> str:
        """요소의 전체 경로 구성"""
        path_parts = []
        current = element

        while current is not None:
            tag = current.tag

            # 네임스페이스 URL을 prefix로 변환
            tag = self.ns_handler.convert_uri(tag, True)

            path_parts.insert(0, tag)
            current = current.getparent()
            # RDF 루트까지만
            if current is not None and "RDF" in current.tag:
                break

        return ".".join(path_parts)

    def _extract_element_data(self, element) -> List[Dict[str, str]]:
        """요소에서 메타데이터 추출"""
        results = []
        base_path = self._build_path(element)

        # 속성이 없는 경우에만 텍스트 값 추가
        if element.text and element.text.strip() and not element.attrib:
            results.append({"metadata_schema": base_path, "value": element.text.strip()})

        # 속성들
        for attr_name, attr_value in element.attrib.items():
            # 네임스페이스가 있는 속성 처리
            if attr_name.startswith("{"):
                attr_name = self.ns_handler.convert_uri(attr_name, True)

            attr_value = self.ns_handler.convert_uri(attr_value)
            attr_key = attr_name  # 전체 prefix 유지

            # 텍스트가 있는 경우: 속성은 스키마에, 텍스트는 값에
            if element.text and element.text.strip():
                schema_path = f"{base_path}.{attr_key}:{attr_value}"
                text_value = element.text.strip()
                results.append({"metadata_schema": schema_path, "value": text_value})
            else:
                # 텍스트가 없는 경우: 속성값을 값으로 사용
                schema_path = f"{base_path}.{attr_key}"
                results.append({"metadata_schema": schema_path, "value": attr_value})

        return results

    def convert_to_table(self, xml_content: str | bytes) -> List[MetadataBase]:
        """XML을 테이블로 변환"""
        try:
            if isinstance(xml_content, bytes):
                root = etree.fromstring(xml_content)
            else:
                root = etree.fromstring(xml_content.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            raise ValueError(f"XML 파싱 오류: {e}")

        all_data = []

        # 모든 요소 순회하여 리프 노드에서 데이터 추출
        for element in root.iter():
            # 리프 노드이거나 텍스트가 있는 노드만 처리
            if (len(element) == 0 and element.text and element.text.strip()) or element.attrib:
                element_data = self._extract_element_data(element)
                all_data.extend(element_data)

        # 결과 생성
        result = []
        for data in all_data:
            if not data["value"]:
                continue  # 빈 값 제외

            result.append(MetadataBase(metadata_schema=data["metadata_schema"], value=data["value"]))

        return result
