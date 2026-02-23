"""OpenAPI examples for column_relation endpoints

Type-safe examples using Pydantic model instances.
"""

from app.src.column_relation.schemas import ColumnRelationCreateParams

# ==================== Example Instances ====================

EXAMPLE_EXACT_MATCH_DCT_TITLE = ColumnRelationCreateParams(
    catalog_column="title", metadata_column="dct:title", correlation=1.0
)

EXAMPLE_EXACT_MATCH_SCHEMA_DESCRIPTION = ColumnRelationCreateParams(
    catalog_column="description", metadata_column="schema:description", correlation=1.0
)

EXAMPLE_HIGH_SIMILARITY_KEYWORD = ColumnRelationCreateParams(
    catalog_column="keyword", metadata_column="dcat:keyword", correlation=0.95
)

EXAMPLE_MODERATE_SIMILARITY_ALTERNATE = ColumnRelationCreateParams(
    catalog_column="title", metadata_column="alternateName", correlation=0.7
)

EXAMPLE_CUSTOM_METADATA = ColumnRelationCreateParams(
    catalog_column="publisher", metadata_column="org:Publisher", correlation=0.98
)

# ==================== OpenAPI Examples Dictionary ====================

COLUMN_RELATION_CREATE_EXAMPLES = {
    "exact_match_dct_title": {
        "summary": "완전 일치 - Dublin Core Title",
        "description": "DCAT 표준의 title과 Dublin Core의 dct:title은 의미가 완전히 동일합니다.",
        "value": EXAMPLE_EXACT_MATCH_DCT_TITLE.model_dump(),
    },
    "exact_match_schema_description": {
        "summary": "완전 일치 - Schema.org Description",
        "description": "DCAT의 description과 Schema.org의 schema:description은 의미가 동일합니다.",
        "value": EXAMPLE_EXACT_MATCH_SCHEMA_DESCRIPTION.model_dump(),
    },
    "high_similarity": {
        "summary": "높은 유사도 - 키워드 매핑",
        "description": "keyword와 dcat:keyword는 거의 동일한 의미이지만 표현 방식이 다를 수 있습니다.",
        "value": EXAMPLE_HIGH_SIMILARITY_KEYWORD.model_dump(),
    },
    "moderate_similarity": {
        "summary": "중간 유사도 - 제목 변형",
        "description": "title과 alternateName은 관련성이 있으나 정확히 동일하지는 않습니다.",
        "value": EXAMPLE_MODERATE_SIMILARITY_ALTERNATE.model_dump(),
    },
    "custom_metadata": {
        "summary": "커스텀 메타데이터 스키마",
        "description": "조직 고유의 메타데이터 스키마를 매핑할 수 있습니다.",
        "value": EXAMPLE_CUSTOM_METADATA.model_dump(),
    },
}
