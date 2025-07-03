from typing import Dict


class NamespaceHandler:
    """네임스페이스 처리 전담 클래스"""

    DEFAULT_NAMESPACES = {
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
        "http://www.w3.org/ns/dcat#": "dcat",
        "http://purl.org/dc/terms/": "dct",
        "http://xmlns.com/foaf/0.1/": "foaf",
        "http://www.w3.org/2006/vcard/ns#": "vcard",
        "http://www.w3.org/XML/1998/namespace": "",
        "http://www.w3.org/2001/XMLSchema#": "",
    }

    def __init__(self, custom_namespaces: Dict[str, str] | None = None):
        """네임스페이스 핸들러 초기화."""
        self.namespaces = {**self.DEFAULT_NAMESPACES}
        if custom_namespaces:
            self.namespaces.update(custom_namespaces)

    def convert_uri(self, uri: str, is_element: bool = False) -> str:
        """URI를 prefix 형태로 변환"""
        for namespace_uri, prefix in self.namespaces.items():
            formatted_ns = f"{{{namespace_uri}}}" if is_element else namespace_uri
            if uri.startswith(formatted_ns):
                return uri.replace(formatted_ns, f"{prefix}:" if prefix else "")
        return uri
