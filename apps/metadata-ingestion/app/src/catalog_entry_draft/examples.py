"""OpenAPI examples for draft endpoints.

Type-safe examples using Pydantic model instances.
"""

from app.src.catalog_entry_draft.model import DraftFieldsUpdateRequest, DraftFieldUpdate

# ==================== Example Instances ====================

EXAMPLE_UPDATE_TITLE = DraftFieldsUpdateRequest(
    updates=[
        DraftFieldUpdate(catalog_field="title", metadata_schema="dct:title"),
    ]
)

EXAMPLE_UPDATE_MULTIPLE_FIELDS = DraftFieldsUpdateRequest(
    updates=[
        DraftFieldUpdate(catalog_field="title", metadata_schema="dct:title"),
        DraftFieldUpdate(catalog_field="description", metadata_schema="schema:description"),
        DraftFieldUpdate(catalog_field="keyword", metadata_schema="dcat:keyword"),
    ]
)

EXAMPLE_UPDATE_PUBLISHER = DraftFieldsUpdateRequest(
    updates=[
        DraftFieldUpdate(catalog_field="publisher", metadata_schema="dct:publisher"),
    ]
)

# ==================== OpenAPI Examples Dictionary ====================

DRAFT_UPDATE_EXAMPLES = {
    "update_title": {
        "summary": "제목 필드 수정",
        "description": "드래프트의 title 필드를 dct:title 메타데이터로 업데이트합니다.",
        "value": EXAMPLE_UPDATE_TITLE.model_dump(),
    },
    "update_multiple": {
        "summary": "여러 필드 동시 수정",
        "description": "title, description, keyword 필드를 한 번에 업데이트합니다.",
        "value": EXAMPLE_UPDATE_MULTIPLE_FIELDS.model_dump(),
    },
    "update_publisher": {
        "summary": "발행자 필드 수정",
        "description": "드래프트의 publisher 필드를 dct:publisher 메타데이터로 업데이트합니다.",
        "value": EXAMPLE_UPDATE_PUBLISHER.model_dump(),
    },
}
