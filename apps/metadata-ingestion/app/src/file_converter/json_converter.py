import json
from typing import Any, Dict, Iterable, List

from app.src.file_converter.converter import Converter
from app.src.metadata_entry.model import MetadataBase


class JsonConverter(Converter):
    """JSON 기반 메타데이터 변환기"""

    def get_supported_extensions(self) -> Iterable[str]:
        """지원하는 파일 확장자 목록 반환"""
        return [".json", ".jsonl", ".jsonld"]

    def convert_to_dict(self, content: bytes) -> Dict[str, Any]:
        """JSON 콘텐츠를 딕셔너리로 변환"""
        return json.loads(content)

    def convert_to_metadata_bases(self, json_content: str | bytes | dict) -> List[MetadataBase]:
        """JSON을 MetadataBase로 변환"""
        if not isinstance(json_content, dict):
            try:
                json_content = json.loads(json_content)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON 파싱 오류: {e}")

        # JSON 평면화
        flattened_data = self._flatten_json(json_content)

        # 결과 생성
        result = []
        for schema, value in flattened_data.items():
            if not value or value.strip() == "":
                continue  # 빈 값 제외

            result.append(MetadataBase(metadata_schema=schema, value=value.strip()))

        return result

    def _flatten_json(self, data: Dict[str, Any], parent_key: str = "", separator: str = ".") -> Dict[str, str]:
        """중첩된 JSON을 평면 구조로 변환"""
        items = []

        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(self._flatten_json(value, new_key, separator).items())
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.extend(self._flatten_json(item, f"{new_key}[{i}]", separator).items())
                    else:
                        items.append((f"{new_key}[{i}]", str(item)))
            else:
                items.append((new_key, str(value)))

        return dict(items)
