"""Tests for file_handler module."""

import io
import json
import zipfile

import pytest

from app.src.file_converter.file_handler import (
    MetadataFile,
    extract_zip,
    process_metadata_file,
    process_metadata_files,
    split_jsonl,
)
from app.src.metadata_entry.model import MetadataSchema


class TestMetadataFile:
    """Test cases for MetadataFile dataclass."""

    def test_get_extension_lowercase(self):
        """Should return lowercase extension."""
        file = MetadataFile(filename="test.JSON", content=b"{}")
        assert file.get_extension() == ".json"

    def test_get_extension_xml(self):
        """Should return .xml extension."""
        file = MetadataFile(filename="data.xml", content=b"<root/>")
        assert file.get_extension() == ".xml"

    def test_get_extension_rdf(self):
        """Should return .rdf extension."""
        file = MetadataFile(filename="data.rdf", content=b"<rdf/>")
        assert file.get_extension() == ".rdf"

    def test_get_extension_no_extension(self):
        """Should return empty string for files without extension."""
        file = MetadataFile(filename="noext", content=b"data")
        assert file.get_extension() == ""

    def test_get_extension_multiple_dots(self):
        """Should return last extension."""
        file = MetadataFile(filename="file.backup.json", content=b"{}")
        assert file.get_extension() == ".json"


class TestSplitJsonl:
    """Test cases for split_jsonl function."""

    def test_split_jsonl_single_line(self):
        """Should split single line JSONL."""
        jsonl_file = MetadataFile(filename="test.jsonl", content=b'{"name": "test"}')
        result = split_jsonl(jsonl_file)

        assert len(result) == 1
        assert result[0].filename == "test.jsonl.0.json"

    def test_split_jsonl_multiple_lines(self):
        """Should split multiple lines."""
        content = b'{"id": 1}\n{"id": 2}\n{"id": 3}'
        jsonl_file = MetadataFile(filename="data.jsonl", content=content)
        result = split_jsonl(jsonl_file)

        assert len(result) == 3
        assert result[0].filename == "data.jsonl.0.json"
        assert result[1].filename == "data.jsonl.1.json"
        assert result[2].filename == "data.jsonl.2.json"

    def test_split_jsonl_skips_empty_lines(self):
        """Should skip empty lines."""
        content = b'{"id": 1}\n\n{"id": 2}\n   \n{"id": 3}'
        jsonl_file = MetadataFile(filename="data.jsonl", content=content)
        result = split_jsonl(jsonl_file)

        assert len(result) == 3

    def test_split_jsonl_preserves_content(self):
        """Should preserve JSON content."""
        content = b'{"name": "test", "value": 123}'
        jsonl_file = MetadataFile(filename="data.jsonl", content=content)
        result = split_jsonl(jsonl_file)

        parsed = json.loads(result[0].content)
        assert parsed["name"] == "test"
        assert parsed["value"] == 123


class TestExtractZip:
    """Test cases for extract_zip function."""

    def test_extract_zip_single_file(self):
        """Should extract single file from ZIP."""
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("test.json", '{"name": "test"}')
        zip_buffer.seek(0)

        zip_file = MetadataFile(filename="archive.zip", content=zip_buffer.read())
        result = extract_zip(zip_file)

        assert len(result) == 1
        assert "test.json" in result[0].filename

    def test_extract_zip_multiple_files(self):
        """Should extract multiple files."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("file1.json", '{"id": 1}')
            zf.writestr("file2.json", '{"id": 2}')
            zf.writestr("file3.xml", "<root/>")
        zip_buffer.seek(0)

        zip_file = MetadataFile(filename="archive.zip", content=zip_buffer.read())
        result = extract_zip(zip_file)

        assert len(result) == 3

    def test_extract_zip_preserves_content(self):
        """Should preserve file content."""
        original_content = b'{"key": "value"}'
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("data.json", original_content)
        zip_buffer.seek(0)

        zip_file = MetadataFile(filename="archive.zip", content=zip_buffer.read())
        result = extract_zip(zip_file)

        assert result[0].content == original_content

    def test_extract_zip_invalid_raises(self):
        """Should raise ValueError on invalid ZIP."""
        zip_file = MetadataFile(filename="bad.zip", content=b"not a zip file")

        with pytest.raises(ValueError) as exc_info:
            extract_zip(zip_file)

        assert "ZIP" in str(exc_info.value)


class TestProcessMetadataFile:
    """Test cases for process_metadata_file function."""

    def test_process_json_file(self):
        """Should process JSON file."""
        file = MetadataFile(filename="test.json", content=b'{"name": "test"}')
        dict_result, schemas = process_metadata_file(file)

        assert isinstance(dict_result, dict)
        assert dict_result["name"] == "test"
        assert isinstance(schemas, list)
        assert all(isinstance(s, MetadataSchema) for s in schemas)

    def test_process_xml_file(self):
        """Should process XML file."""
        file = MetadataFile(filename="test.xml", content=b"<root><title>Test</title></root>")
        dict_result, schemas = process_metadata_file(file)

        assert isinstance(dict_result, dict)
        assert isinstance(schemas, list)

    def test_process_rdf_file(self):
        """Should process RDF file."""
        content = b"""<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <rdf:Description>
                <title>Test</title>
            </rdf:Description>
        </rdf:RDF>
        """
        file = MetadataFile(filename="test.rdf", content=content)
        dict_result, schemas = process_metadata_file(file)

        assert isinstance(dict_result, dict)
        assert isinstance(schemas, list)

    def test_process_unsupported_file_raises(self):
        """Should raise ValueError for unsupported file types."""
        file = MetadataFile(filename="test.txt", content=b"plain text")

        with pytest.raises(ValueError) as exc_info:
            process_metadata_file(file)

        assert "Unsupported" in str(exc_info.value) or "Error" in str(exc_info.value)

    def test_process_invalid_json_raises(self):
        """Should raise ValueError for invalid JSON."""
        file = MetadataFile(filename="bad.json", content=b"not json")

        with pytest.raises(ValueError):
            process_metadata_file(file)


class TestProcessMetadataFiles:
    """Test cases for process_metadata_files function."""

    def test_process_single_json_file(self):
        """Should process single JSON file."""
        files = [MetadataFile(filename="test.json", content=b'{"name": "test"}')]
        results, errors = process_metadata_files(files)

        assert len(results) == 1
        assert len(errors) == 0

    def test_process_multiple_files(self):
        """Should process multiple files."""
        files = [
            MetadataFile(filename="file1.json", content=b'{"id": 1}'),
            MetadataFile(filename="file2.json", content=b'{"id": 2}'),
        ]
        results, errors = process_metadata_files(files)

        assert len(results) == 2
        assert len(errors) == 0

    def test_process_zip_file(self):
        """Should extract and process ZIP contents."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("inner.json", '{"name": "from zip"}')
        zip_buffer.seek(0)

        files = [MetadataFile(filename="archive.zip", content=zip_buffer.read())]
        results, errors = process_metadata_files(files)

        assert len(results) == 1
        assert len(errors) == 0

    def test_process_jsonl_file(self):
        """Should split and process JSONL contents."""
        content = b'{"id": 1}\n{"id": 2}'
        files = [MetadataFile(filename="data.jsonl", content=content)]
        results, errors = process_metadata_files(files)

        assert len(results) == 2
        assert len(errors) == 0

    def test_process_with_errors_collects_errors(self):
        """Should collect errors without stopping."""
        files = [
            MetadataFile(filename="good.json", content=b'{"name": "valid"}'),
            MetadataFile(filename="bad.json", content=b"invalid json"),
            MetadataFile(filename="also_good.json", content=b'{"name": "also valid"}'),
        ]
        results, errors = process_metadata_files(files)

        assert len(results) == 2
        assert len(errors) == 1
        assert "bad.json" in errors[0]["filename"]

    def test_process_mixed_file_types(self):
        """Should process mixed file types."""
        files = [
            MetadataFile(filename="data.json", content=b'{"type": "json"}'),
            MetadataFile(filename="data.xml", content=b"<root><type>xml</type></root>"),
        ]
        results, errors = process_metadata_files(files)

        assert len(results) == 2
        assert len(errors) == 0

    def test_process_empty_list(self):
        """Should handle empty file list."""
        results, errors = process_metadata_files([])

        assert len(results) == 0
        assert len(errors) == 0


class TestProcessMetadataFilesWithSamples:
    """Test process_metadata_files with actual sample files."""

    def test_process_sample_json_files(self, sample_json_files):
        """Should process all sample JSON files."""
        files = [MetadataFile(filename=name, content=content) for name, content in sample_json_files.items()]
        results, errors = process_metadata_files(files)

        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == len(sample_json_files)

    def test_process_sample_rdf_files(self, sample_rdf_files):
        """Should process all sample RDF files."""
        files = [MetadataFile(filename=name, content=content) for name, content in sample_rdf_files.items()]
        results, errors = process_metadata_files(files)

        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == len(sample_rdf_files)

    def test_process_sample_xml_files(self, sample_xml_files):
        """Should process all sample XML files."""
        files = [MetadataFile(filename=name, content=content) for name, content in sample_xml_files.items()]
        results, errors = process_metadata_files(files)

        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == len(sample_xml_files)
