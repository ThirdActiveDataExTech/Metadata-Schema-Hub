from typing import Any, Dict

# Example: Schema.org basic metadata
FORM_EXAMPLE_SCHEMA_ORG_BASIC = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "서울시 대중교통 이용 현황",
    "description": "서울시 지하철 및 버스 이용 통계 데이터",
    "publisher": {"@type": "Organization", "name": "서울시"},
}

# Example: Schema.org detailed metadata
FORM_EXAMPLE_SCHEMA_ORG_DETAILED = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "공공데이터포털 교통 데이터",
    "description": "전국 교통 흐름 및 사고 데이터셋",
    "keywords": ["교통", "데이터", "공공"],
    "creator": {"@type": "Organization", "name": "국토교통부"},
    "datePublished": "2024-01-15",
    "dateModified": "2024-11-20",
    "license": "CC-BY-4.0",
}

# Example: DCAT basic metadata
FORM_EXAMPLE_DCAT_BASIC = {
    "dct:title": "환경 데이터셋",
    "dct:description": "대기질 측정 데이터",
    "dct:publisher": "환경부",
    "dcat:keyword": ["환경", "대기질"],
}

# Example: Custom minimal metadata
FORM_EXAMPLE_CUSTOM_MINIMAL = {
    "title": "문화시설 정보",
    "description": "전국 문화시설 목록 및 위치 정보",
    "author": "문화체육관광부",
}

# Example: Custom detailed metadata
FORM_EXAMPLE_CUSTOM_DETAILED = {
    "title": "스마트시티 센서 데이터",
    "description": "IoT 센서를 통해 수집된 도시 환경 데이터",
    "keywords": ["스마트시티", "IoT", "센서"],
    "publisher": "서울시 스마트시티과",
    "issued_date": "2024-03-01",
    "modified_date": "2024-11-26",
    "license": "공공누리 제1유형",
    "contact": "smartcity@seoul.go.kr",
    "access_url": "https://data.seoul.go.kr/sensors",
}


# OpenAPI Examples Dictionary
METADATA_FORM_EXAMPLES: Dict[str, Dict[str, Any]] = {
    "schema_org_basic": {
        "summary": "Schema.org 기본 메타데이터",
        "description": "Schema.org Dataset 타입의 최소 필수 필드",
        "value": FORM_EXAMPLE_SCHEMA_ORG_BASIC,
    },
    "schema_org_detailed": {
        "summary": "Schema.org 상세 메타데이터",
        "description": "Schema.org Dataset 타입의 전체 필드 (키워드, 라이선스 포함)",
        "value": FORM_EXAMPLE_SCHEMA_ORG_DETAILED,
    },
    "dcat_basic": {
        "summary": "DCAT 기본 메타데이터",
        "description": "Dublin Core Terms와 DCAT 어휘를 사용한 메타데이터",
        "value": FORM_EXAMPLE_DCAT_BASIC,
    },
    "custom_minimal": {
        "summary": "사용자 정의 최소 메타데이터",
        "description": "필수 정보만 포함한 간단한 커스텀 메타데이터",
        "value": FORM_EXAMPLE_CUSTOM_MINIMAL,
    },
    "custom_detailed": {
        "summary": "사용자 정의 상세 메타데이터",
        "description": "전체 정보를 포함한 상세 커스텀 메타데이터",
        "value": FORM_EXAMPLE_CUSTOM_DETAILED,
    },
}
