import json
from typing import List, Dict, Any

from app.src.metadata_entry.metadata_entry import MetadataEntry


class JsonConverter:
    """JSON 기반 메타데이터 변환기"""

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

    def convert_to_table(self, json_content: str | bytes, metadata_id: str | None = None) -> List[MetadataEntry]:
        """JSON을 테이블로 변환"""
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 오류: {e}")

        # JSON 평면화
        flattened_data = self._flatten_json(data)

        # 결과 생성
        result = []
        for (schema, value) in flattened_data.items():
            if not value or value.strip() == "":
                continue  # 빈 값 제외

            result.append(MetadataEntry(
                id=None,
                metadata_id=metadata_id,
                metadata_schema=schema,
                value=value.strip()
            ))

        return result
