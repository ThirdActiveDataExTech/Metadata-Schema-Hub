"""Tests for LxmlConverter (XML/RDF)."""

import pytest
from lxml import etree

from app.src.file_converter.xml_converter import LxmlConverter
from app.src.metadata_entry.model import MetadataSchema


class TestLxmlConverter:
    """Test cases for LxmlConverter."""

    @pytest.fixture
    def converter(self):
        """Create LxmlConverter instance."""
        return LxmlConverter()

    # ========================================================================
    # get_supported_extensions tests
    # ========================================================================

    def test_get_supported_extensions(self, converter):
        """Should return correct extensions."""
        extensions = list(converter.get_supported_extensions())
        assert ".rdf" in extensions
        assert ".xml" in extensions
        assert len(extensions) == 2

    # ========================================================================
    # convert_to_dict tests
    # ========================================================================

    def test_convert_to_dict_valid_xml(self, converter):
        """Should parse valid XML to dict."""
        content = b"<root><name>test</name></root>"
        result = converter.convert_to_dict(content)
        assert result["root"]["name"] == "test"

    def test_convert_to_dict_with_attributes(self, converter):
        """Should include attributes in dict."""
        content = b'<root attr="value"><name>test</name></root>'
        result = converter.convert_to_dict(content)
        assert "@attr" in result["root"]
        assert result["root"]["@attr"] == "value"

    # ========================================================================
    # convert_to_metadata_schemas tests
    # ========================================================================

    def test_convert_to_metadata_schemas_simple_xml(self, converter):
        """Should convert simple XML to MetadataSchema list."""
        content = b"<root><title>Test Title</title></root>"
        result = converter.convert_to_metadata_schemas(content)

        assert len(result) >= 1
        assert all(isinstance(s, MetadataSchema) for s in result)

        schemas = {s.metadata_schema: s.value for s in result}
        assert any("title" in k for k in schemas.keys())

    def test_convert_to_metadata_schemas_with_namespace(self, converter):
        """Should handle XML with namespaces."""
        content = b"""<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                 xmlns:dct="http://purl.org/dc/terms/">
            <rdf:Description>
                <dct:title>Namespaced Title</dct:title>
            </rdf:Description>
        </rdf:RDF>
        """
        result = converter.convert_to_metadata_schemas(content)

        assert len(result) >= 1
        schemas = {s.metadata_schema: s.value for s in result}
        # Should have converted namespace prefix
        assert any("dct:title" in k for k in schemas.keys())

    def test_convert_to_metadata_schemas_with_attributes(self, converter):
        """Should extract attributes."""
        content = b"""<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <rdf:Description rdf:about="http://example.org/resource">
            </rdf:Description>
        </rdf:RDF>
        """
        result = converter.convert_to_metadata_schemas(content)

        schemas = {s.metadata_schema: s.value for s in result}
        # Should have attribute in path
        assert any("about" in k or "rdf:about" in k for k in schemas.keys())

    def test_convert_to_metadata_schemas_invalid_xml_raises(self, converter):
        """Should raise ValueError on invalid XML."""
        with pytest.raises(ValueError) as exc_info:
            converter.convert_to_metadata_schemas(b"<broken xml")

        assert "XML" in str(exc_info.value)

    def test_convert_to_metadata_schemas_empty_elements_excluded(self, converter):
        """Should exclude empty elements."""
        content = b"<root><empty></empty><filled>value</filled></root>"
        result = converter.convert_to_metadata_schemas(content)

        values = {s.value for s in result}
        assert "value" in values
        assert "" not in values

    # ========================================================================
    # Sample RDF file tests
    # ========================================================================

    def test_dcat_rdf_parsing(self, converter, sample_dcat_rdf):
        """Should parse DCAT RDF format."""
        result = converter.convert_to_metadata_schemas(sample_dcat_rdf)

        assert len(result) > 0
        assert all(isinstance(s, MetadataSchema) for s in result)

        # Check for DCAT vocabulary presence
        schemas = {s.metadata_schema for s in result}
        has_dcat = any("dcat:" in s or "dct:" in s for s in schemas)
        assert has_dcat, "Should have DCAT/DCT prefixed schemas"

    def test_all_rdf_samples_parse_without_error(self, converter, sample_rdf_files):
        """All RDF sample files should parse without errors."""
        for filename, content in sample_rdf_files.items():
            result = converter.convert_to_metadata_schemas(content)
            assert isinstance(result, list), f"Failed for {filename}"
            assert all(isinstance(s, MetadataSchema) for s in result), f"Invalid schema in {filename}"

    def test_rdf_samples_produce_non_empty_results(self, converter, sample_rdf_files):
        """RDF sample files should produce non-empty schema lists."""
        for filename, content in sample_rdf_files.items():
            result = converter.convert_to_metadata_schemas(content)
            assert len(result) > 0, f"Empty result for {filename}"

    # ========================================================================
    # Sample XML file tests (SDMX)
    # ========================================================================

    def test_kosis_xml_parsing(self, converter, sample_kosis_xml):
        """Should parse KOSIS SDMX XML format."""
        result = converter.convert_to_metadata_schemas(sample_kosis_xml)

        assert len(result) > 0
        assert all(isinstance(s, MetadataSchema) for s in result)

        # Should have SDMX namespace prefixes
        schemas = {s.metadata_schema for s in result}
        has_sdmx = any("sdmx" in s for s in schemas)
        assert has_sdmx, "Should have SDMX prefixed schemas"

    def test_all_xml_samples_parse_without_error(self, converter, sample_xml_files):
        """All XML sample files should parse without errors."""
        for filename, content in sample_xml_files.items():
            result = converter.convert_to_metadata_schemas(content)
            assert isinstance(result, list), f"Failed for {filename}"
            assert all(isinstance(s, MetadataSchema) for s in result), f"Invalid schema in {filename}"


class TestBuildPath:
    """Test cases for _build_path internal method."""

    @pytest.fixture
    def converter(self):
        """Create LxmlConverter instance."""
        return LxmlConverter()

    def test_build_path_simple_element(self, converter):
        """Should build path for simple element."""
        

        root = etree.fromstring(b"<root><child>value</child></root>")
        child = root.find("child")
        path = converter._build_path(child)

        assert "child" in path

    def test_build_path_nested_element(self, converter):
        """Should build path with dot separator for nested elements."""

        root = etree.fromstring(b"<root><parent><child>value</child></parent></root>")
        child = root.find(".//child")
        path = converter._build_path(child)

        assert "." in path
        assert "child" in path


class TestExtractElementData:
    """Test cases for _extract_element_data internal method."""

    @pytest.fixture
    def converter(self):
        """Create LxmlConverter instance."""
        return LxmlConverter()

    def test_extract_element_with_text(self, converter):
        """Should extract text from element."""

        root = etree.fromstring(b"<root><title>Test</title></root>")
        element = root.find("title")
        data = converter._extract_element_data(element)

        assert len(data) == 1
        assert data[0]["value"] == "Test"

    def test_extract_element_with_attribute(self, converter):
        """Should extract attributes."""

        root = etree.fromstring(b'<root><item id="123"/></root>')
        element = root.find("item")
        data = converter._extract_element_data(element)

        assert len(data) >= 1
        values = [d["value"] for d in data]
        assert "123" in values

    def test_extract_element_with_text_and_attribute(self, converter):
        """Should handle element with both text and attributes."""

        content = b"""<?xml version="1.0"?>
        <root xmlns:xml="http://www.w3.org/XML/1998/namespace">
            <title xml:lang="en">English Title</title>
        </root>
        """
        root = etree.fromstring(content)
        element = root.find("title")
        data = converter._extract_element_data(element)

        # Should combine attribute info with text
        assert len(data) >= 1
        values = [d["value"] for d in data]
        assert "English Title" in values
