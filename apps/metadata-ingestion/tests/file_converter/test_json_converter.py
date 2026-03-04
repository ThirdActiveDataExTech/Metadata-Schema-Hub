"""Tests for JsonConverter."""

import json

import pytest

from app.src.file_converter.json_converter import JsonConverter
from app.src.metadata_entry.model import MetadataSchema


class TestJsonConverter:
    """Test cases for JsonConverter."""

    @pytest.fixture
    def converter(self):
        """Create JsonConverter instance."""
        return JsonConverter()

    # ========================================================================
    # get_supported_extensions tests
    # ========================================================================

    def test_get_supported_extensions(self, converter):
        """Should return correct extensions."""
        extensions = list(converter.get_supported_extensions())
        assert ".json" in extensions
        assert ".jsonl" in extensions
        assert ".jsonld" in extensions
        assert len(extensions) == 3

    # ========================================================================
    # convert_to_dict tests
    # ========================================================================

    def test_convert_to_dict_valid_json(self, converter):
        """Should parse valid JSON to dict."""
        content = b'{"name": "test", "value": 123}'
        result = converter.convert_to_dict(content)
        assert result == {"name": "test", "value": 123}

    def test_convert_to_dict_nested_json(self, converter):
        """Should parse nested JSON."""
        content = b'{"outer": {"inner": "value"}}'
        result = converter.convert_to_dict(content)
        assert result["outer"]["inner"] == "value"

    def test_convert_to_dict_invalid_json_raises(self, converter):
        """Should raise on invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            converter.convert_to_dict(b"not a json")

    # ========================================================================
    # convert_to_metadata_schemas tests
    # ========================================================================

    def test_convert_to_metadata_schemas_simple(self, converter):
        """Should convert simple JSON to MetadataSchema list."""
        content = b'{"name": "test dataset"}'
        result = converter.convert_to_metadata_schemas(content)

        assert len(result) == 1
        assert isinstance(result[0], MetadataSchema)
        assert result[0].metadata_schema == "name"
        assert result[0].value == "test dataset"

    def test_convert_to_metadata_schemas_multiple_fields(self, converter):
        """Should convert multiple fields."""
        content = b'{"name": "dataset", "description": "A description"}'
        result = converter.convert_to_metadata_schemas(content)

        assert len(result) == 2
        schemas = {s.metadata_schema: s.value for s in result}
        assert schemas["name"] == "dataset"
        assert schemas["description"] == "A description"

    def test_convert_to_metadata_schemas_nested(self, converter):
        """Should flatten nested structures with dot notation."""
        content = b'{"person": {"name": "John", "age": "30"}}'
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema: s.value for s in result}
        assert "person.name" in schemas
        assert "person.age" in schemas
        assert schemas["person.name"] == "John"

    def test_convert_to_metadata_schemas_deep_nesting(self, converter):
        """Should handle deeply nested structures."""
        content = b'{"level1": {"level2": {"level3": "deep value"}}}'
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema: s.value for s in result}
        assert "level1.level2.level3" in schemas
        assert schemas["level1.level2.level3"] == "deep value"

    def test_convert_to_metadata_schemas_array_of_primitives(self, converter):
        """Should join primitive arrays with comma."""
        content = b'{"tags": ["python", "fastapi", "test"]}'
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema: s.value for s in result}
        assert "tags" in schemas
        assert schemas["tags"] == "python, fastapi, test"

    def test_convert_to_metadata_schemas_array_of_objects(self, converter):
        """Should index array of objects."""
        content = b'{"items": [{"name": "first"}, {"name": "second"}]}'
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema: s.value for s in result}
        assert "items[0].name" in schemas
        assert "items[1].name" in schemas
        assert schemas["items[0].name"] == "first"
        assert schemas["items[1].name"] == "second"

    def test_convert_to_metadata_schemas_empty_string_excluded(self, converter):
        """Should exclude empty string values."""
        content = b'{"name": "test", "empty": ""}'
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema for s in result}
        assert "name" in schemas
        assert "empty" not in schemas

    def test_convert_to_metadata_schemas_whitespace_only_excluded(self, converter):
        """Should exclude whitespace-only values."""
        content = b'{"name": "test", "whitespace": "   "}'
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema for s in result}
        assert "name" in schemas
        assert "whitespace" not in schemas

    def test_convert_to_metadata_schemas_strips_whitespace(self, converter):
        """Should strip whitespace from values."""
        content = b'{"name": "  test value  "}'
        result = converter.convert_to_metadata_schemas(content)

        assert result[0].value == "test value"

    def test_convert_to_metadata_schemas_number_to_string(self, converter):
        """Should convert numbers to strings."""
        content = b'{"count": 42, "price": 19.99}'
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema: s.value for s in result}
        assert schemas["count"] == "42"
        assert schemas["price"] == "19.99"

    def test_convert_to_metadata_schemas_boolean_to_string(self, converter):
        """Should convert booleans to strings."""
        content = b'{"active": true, "deleted": false}'
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema: s.value for s in result}
        assert schemas["active"] == "True"
        assert schemas["deleted"] == "False"

    def test_convert_to_metadata_schemas_invalid_json_raises(self, converter):
        """Should raise ValueError on invalid JSON."""
        with pytest.raises(ValueError) as exc_info:
            converter.convert_to_metadata_schemas(b"not json")

        assert "JSON" in str(exc_info.value)

    # ========================================================================
    # Sample file tests
    # ========================================================================

    def test_schema_org_json_parsing(self, converter, sample_schema_org_json):
        """Should parse schema.org format JSON."""
        result = converter.convert_to_metadata_schemas(sample_schema_org_json)

        assert len(result) > 0
        assert all(isinstance(s, MetadataSchema) for s in result)

        # Check for expected schema.org fields
        schemas = {s.metadata_schema for s in result}
        # Should have @context, @type, name, description etc.
        assert any("@context" in s or "name" in s for s in schemas)

    def test_all_json_samples_parse_without_error(self, converter, sample_json_files):
        """All JSON sample files should parse without errors."""
        for filename, content in sample_json_files.items():
            result = converter.convert_to_metadata_schemas(content)
            assert isinstance(result, list), f"Failed for {filename}"
            assert all(isinstance(s, MetadataSchema) for s in result), f"Invalid schema in {filename}"

    def test_json_samples_produce_non_empty_results(self, converter, sample_json_files):
        """JSON sample files should produce non-empty schema lists."""
        for filename, content in sample_json_files.items():
            result = converter.convert_to_metadata_schemas(content)
            assert len(result) > 0, f"Empty result for {filename}"


class TestFlattenJson:
    """Test cases for _flatten_json internal method."""

    @pytest.fixture
    def converter(self):
        """Create JsonConverter instance."""
        return JsonConverter()

    def test_flatten_simple_dict(self, converter):
        """Should flatten simple dict."""
        data = {"key": "value"}
        result = converter._flatten_json(data)
        assert result == {"key": "value"}

    def test_flatten_nested_dict(self, converter):
        """Should flatten nested dict with dot separator."""
        data = {"outer": {"inner": "value"}}
        result = converter._flatten_json(data)
        assert result == {"outer.inner": "value"}

    def test_flatten_mixed_array(self, converter):
        """Should handle arrays with mixed content."""
        data = {"items": [{"id": "1"}, "simple", {"id": "2"}]}
        result = converter._flatten_json(data)

        assert "items[0].id" in result
        assert "items[2].id" in result
        assert "items" in result  # simple string goes to parent key

    def test_flatten_empty_dict(self, converter):
        """Should handle empty dict."""
        data = {}
        result = converter._flatten_json(data)
        assert result == {}

    def test_flatten_preserves_order(self, converter):
        """Should preserve key order."""
        data = {"a": "1", "b": "2", "c": "3"}
        result = converter._flatten_json(data)
        keys = list(result.keys())
        assert keys == ["a", "b", "c"]
