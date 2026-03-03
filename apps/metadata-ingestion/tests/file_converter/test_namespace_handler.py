"""Tests for NamespaceHandler."""

from app.src.file_converter.namespace_handler import NamespaceHandler


class TestNamespaceHandler:
    """Test cases for NamespaceHandler."""

    def test_default_namespaces_contains_rdf(self):
        """Default namespaces should contain RDF."""
        handler = NamespaceHandler()
        assert "http://www.w3.org/1999/02/22-rdf-syntax-ns#" in handler.namespaces

    def test_default_namespaces_contains_dcat(self):
        """Default namespaces should contain DCAT."""
        handler = NamespaceHandler()
        assert "http://www.w3.org/ns/dcat#" in handler.namespaces

    def test_default_namespaces_contains_dct(self):
        """Default namespaces should contain DCT."""
        handler = NamespaceHandler()
        assert "http://purl.org/dc/terms/" in handler.namespaces

    def test_default_namespaces_contains_foaf(self):
        """Default namespaces should contain FOAF."""
        handler = NamespaceHandler()
        assert "http://xmlns.com/foaf/0.1/" in handler.namespaces

    def test_default_namespaces_contains_sdmx(self):
        """Default namespaces should contain SDMX namespaces."""
        handler = NamespaceHandler()
        assert "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" in handler.namespaces
        assert "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common" in handler.namespaces
        assert "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure" in handler.namespaces

    def test_convert_uri_element_rdf(self):
        """Convert element URI with RDF namespace."""
        handler = NamespaceHandler()
        result = handler.convert_uri("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF", is_element=True)
        assert result == "rdf:RDF"

    def test_convert_uri_element_dcat(self):
        """Convert element URI with DCAT namespace."""
        handler = NamespaceHandler()
        result = handler.convert_uri("{http://www.w3.org/ns/dcat#}Dataset", is_element=True)
        assert result == "dcat:Dataset"

    def test_convert_uri_element_dct(self):
        """Convert element URI with DCT namespace."""
        handler = NamespaceHandler()
        result = handler.convert_uri("{http://purl.org/dc/terms/}title", is_element=True)
        assert result == "dct:title"

    def test_convert_uri_attribute_value(self):
        """Convert attribute value URI."""
        handler = NamespaceHandler()
        result = handler.convert_uri("http://www.w3.org/ns/dcat#Distribution", is_element=False)
        assert result == "dcat:Distribution"

    def test_convert_uri_unknown_namespace(self):
        """Unknown namespace should return original URI."""
        handler = NamespaceHandler()
        unknown_uri = "{http://unknown.namespace/}element"
        result = handler.convert_uri(unknown_uri, is_element=True)
        assert result == unknown_uri

    def test_convert_uri_empty_prefix_namespace(self):
        """Namespace with empty prefix should remove namespace without prefix."""
        handler = NamespaceHandler()
        result = handler.convert_uri("{http://www.w3.org/XML/1998/namespace}lang", is_element=True)
        assert result == "lang"

    def test_custom_namespace_addition(self):
        """Custom namespace should be added and usable."""
        custom_ns = {"http://custom.namespace/": "custom"}
        handler = NamespaceHandler(custom_namespaces=custom_ns)
        result = handler.convert_uri("{http://custom.namespace/}element", is_element=True)
        assert result == "custom:element"

    def test_custom_namespace_override(self):
        """Custom namespace should override default."""
        custom_ns = {"http://www.w3.org/ns/dcat#": "mydcat"}
        handler = NamespaceHandler(custom_namespaces=custom_ns)
        result = handler.convert_uri("{http://www.w3.org/ns/dcat#}Dataset", is_element=True)
        assert result == "mydcat:Dataset"

    def test_convert_uri_sdmx_message(self):
        """Convert SDMX message namespace."""
        handler = NamespaceHandler()
        result = handler.convert_uri("{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message}Structure", is_element=True)
        assert result == "sdmx-msg:Structure"

    def test_convert_uri_sdmx_structure(self):
        """Convert SDMX structure namespace."""
        handler = NamespaceHandler()
        result = handler.convert_uri(
            "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}CategoryScheme", is_element=True
        )
        assert result == "sdmx-str:CategoryScheme"
