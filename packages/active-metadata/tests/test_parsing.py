"""Unit tests for parsing utility functions."""

from datetime import date

import pytest

from active_metadata.parsing import convert_field_types, detect_extension, parse_date, to_str_list


class TestParseDate:
    """Tests for parse_date."""

    def test_iso_format(self):
        """Test ISO 8601 format."""
        assert parse_date("2024-01-15") == date(2024, 1, 15)
        assert parse_date("2024/01/15") == date(2024, 1, 15)

    def test_european_format(self):
        """Test European format (dd-mm-yyyy)."""
        assert parse_date("15-01-2024") == date(2024, 1, 15)
        assert parse_date("15/01/2024") == date(2024, 1, 15)

    def test_compact_format(self):
        """Test compact format (yyyymmdd)."""
        assert parse_date("20240115") == date(2024, 1, 15)

    def test_iso_with_time(self):
        """Test ISO format with time component."""
        assert parse_date("2024-01-15T10:30:00Z") == date(2024, 1, 15)
        assert parse_date("2024-01-15T10:30:00+09:00") == date(2024, 1, 15)

    def test_already_date(self):
        """Test with date object input."""
        d = date(2024, 1, 15)
        assert parse_date(d) == d

    def test_none_and_empty(self):
        """Test None and empty inputs."""
        assert parse_date(None) is None
        assert parse_date("") is None
        assert parse_date("   ") is None

    def test_invalid(self):
        """Test invalid date strings."""
        assert parse_date("not-a-date") is None
        assert parse_date("2024-13-45") is None


class TestToStrList:
    """Tests for to_str_list."""

    def test_plain_string(self):
        """Test with plain string."""
        assert to_str_list("test") == ["test"]

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            pytest.param("a, b, c", ["a", "b", "c"], id="comma_spaced"),
            pytest.param("a,b,c", ["a", "b", "c"], id="comma"),
            pytest.param("a; b; c", ["a", "b", "c"], id="semicolon_spaced"),
            pytest.param("a;b;c", ["a", "b", "c"], id="semicolon"),
            pytest.param("a/b/c", ["a", "b", "c"], id="slash"),
            pytest.param("a|b|c", ["a", "b", "c"], id="pipe"),
            pytest.param("a@b@c", ["a", "b", "c"], id="at"),
        ],
    )
    def test_separated_strings(self, input_str: str, expected: list[str]):
        """Test with various separator-delimited strings."""
        assert to_str_list(input_str) == expected

    def test_list_input(self):
        """Test with list input."""
        assert to_str_list(["x", "y", "z"]) == ["x", "y", "z"]
        assert to_str_list([1, "y", "z"]) == ["1", "y", "z"]

    def test_empty_input(self):
        """Test with empty input."""
        assert to_str_list("") == []
        assert to_str_list([]) == []
        assert to_str_list(None) == []

    def test_whitespace_handling(self):
        """Test with whitespace handling."""
        assert to_str_list("  a  ,  b  ,  c  ") == ["a", "b", "c"]
        assert to_str_list("   ") == []

    def test_other_types(self):
        """Test with non-string/list types."""
        assert to_str_list(123) == ["123"]
        assert to_str_list(3.14) == ["3.14"]


class TestDetectExtension:
    """Tests for detect_extension."""

    def test_from_filename(self):
        """Test extension detection from filename."""
        assert detect_extension(b"content", "file.json") == "json"
        assert detect_extension(b"content", "file.xml") == "xml"
        assert detect_extension(b"content", "data.rdf") == "rdf"
        assert detect_extension(b"content", "archive.tar.gz") == "gz"

    def test_xml_content(self):
        """Test XML content detection."""
        assert detect_extension('<?xml version="1.0"?><root></root>', None) == "xml"
        assert detect_extension('<rdf:RDF xmlns:rdf="..."></rdf:RDF>', None) == "xml"

    def test_json_content(self):
        """Test JSON content detection."""
        assert detect_extension('{"key": "value"}', None) == "json"
        assert detect_extension('[1, 2, 3]', None) == "json"

    def test_binary_fallback(self):
        """Test fallback to 'bin' for unknown content."""
        assert detect_extension(b"\x00\x01\x02", None) == "bin"
        assert detect_extension("plain text", None) == "bin"
        assert detect_extension("", None) == "bin"

    def test_with_whitespace(self):
        """Test content detection with leading/trailing whitespace."""
        assert detect_extension('  \n{"key": "value"}\n  ', None) == "json"
        assert detect_extension('  \n<?xml version="1.0"?>\n  ', None) == "xml"

    def test_filename_priority(self):
        """Test that filename takes priority over content detection."""
        json_content = '{"key": "value"}'
        assert detect_extension(json_content, "data.xml") == "xml"


class TestConvertFieldTypes:
    """Tests for convert_field_types with atomic_list_fields."""

    def test_list_fields_split_by_separator(self):
        """list_fields는 구분자로 분리되어야 함."""
        result = convert_field_types(
            {"keyword": "에너지,태양광,전기사업"},
            list_fields=["keyword"],
            date_fields=[],
        )
        assert result["keyword"] == ["에너지", "태양광", "전기사업"]

    def test_atomic_list_fields_url_not_split(self):
        """atomic_list_fields는 URL을 분리하지 않아야 함."""
        url = "https://www.data.go.kr/data/15107742/standard.do"
        result = convert_field_types(
            {"external_ids": url},
            list_fields=[],
            date_fields=[],
            atomic_list_fields=["external_ids"],
        )
        assert result["external_ids"] == [url]

    def test_atomic_list_fields_already_list(self):
        """atomic_list_fields에 이미 list가 들어오면 그대로 유지."""
        urls = ["https://example.com/1", "https://example.com/2"]
        result = convert_field_types(
            {"external_ids": urls},
            list_fields=[],
            date_fields=[],
            atomic_list_fields=["external_ids"],
        )
        assert result["external_ids"] == urls

    def test_atomic_list_fields_empty(self):
        """atomic_list_fields에 빈 값이면 None."""
        result = convert_field_types(
            {"external_ids": ""},
            list_fields=[],
            date_fields=[],
            atomic_list_fields=["external_ids"],
        )
        assert result["external_ids"] is None

    def test_atomic_list_fields_none(self):
        """atomic_list_fields에 None이면 None."""
        result = convert_field_types(
            {"external_ids": None},
            list_fields=[],
            date_fields=[],
            atomic_list_fields=["external_ids"],
        )
        assert result["external_ids"] is None

    def test_mixed_fields(self):
        """list_fields, date_fields, atomic_list_fields 혼합."""
        result = convert_field_types(
            {
                "keyword": "a,b,c",
                "issued": "2024-01-15",
                "external_ids": "https://example.com/dataset/123",
            },
            list_fields=["keyword"],
            date_fields=["issued"],
            atomic_list_fields=["external_ids"],
        )
        assert result["keyword"] == ["a", "b", "c"]
        assert result["issued"] == date(2024, 1, 15)
        assert result["external_ids"] == ["https://example.com/dataset/123"]

    def test_backward_compatible_without_atomic(self):
        """atomic_list_fields 미전달 시 기존 동작 유지."""
        result = convert_field_types(
            {"keyword": "a,b", "title": "test"},
            list_fields=["keyword"],
            date_fields=[],
        )
        assert result["keyword"] == ["a", "b"]
        assert result["title"] == "test"
