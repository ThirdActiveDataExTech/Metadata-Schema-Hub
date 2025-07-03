import io
import json
import logging
import pathlib
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from app.src.file_converter.json_converter import JsonConverter
from app.src.file_converter.xml_converter import LxmlConverter
from app.src.metadata_entry.model import MetadataBase

json_converter = JsonConverter()
xml_converter = LxmlConverter()


@dataclass
class MetadataFile:
    """Metadata file representation."""

    filename: str
    content: bytes

    def get_extension(self) -> str:
        """Get the file extension."""
        return pathlib.Path(self.filename).suffix.lower()


def split_jsonl(jsonl_file: MetadataFile) -> List[MetadataFile]:
    """Process JSONL content and return a list of dictionaries."""
    try:
        return [
            MetadataFile(f"{jsonl_file.filename}.{i}.json", line.encode("utf-8"))
            for i, line in enumerate(jsonl_file.content.decode("utf-8").splitlines())
            if line.strip()
        ]
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSONL: {e}")
        raise ValueError("Invalid JSONL format.") from e


def extract_zip(zip_file: MetadataFile) -> List[MetadataFile]:
    """Extract files from a ZIP archive and return their contents and any errors."""
    try:
        with zipfile.ZipFile(io.BytesIO(zip_file.content)) as zf:
            return [
                MetadataFile(f"{zip_file.filename}.{extracted_file.filename}", zf.read(extracted_file))
                for extracted_file in zf.infolist()
            ]
    except zipfile.BadZipFile as e:
        logging.error(f"Failed to extract ZIP file: {e}")
        raise ValueError("Invalid ZIP file format.") from e


def process_metadata_file(file: MetadataFile) -> Tuple[Dict[str, Any], List[MetadataBase]]:
    """Process a metadata file based on its extension."""
    try:
        if file.get_extension() in json_converter.get_supported_extensions():
            return json_converter.convert_to_dict(file.content), json_converter.convert_to_metadata_bases(file.content)
        elif file.get_extension() in xml_converter.get_supported_extensions():
            return xml_converter.convert_to_dict(file.content), xml_converter.convert_to_metadata_bases(file.content)
        else:
            raise ValueError(f"Unsupported file type: {file.filename}")
    except Exception as e:
        raise ValueError(f"Error processing file {file.filename}: {str(e)}") from e


def process_metadata_files(
    files: List[MetadataFile],
) -> Tuple[List[Tuple[Dict[str, Any], List[MetadataBase]]], List[Dict[str, str]]]:
    """Process multiple metadata files and return their contents and errors if any."""
    metadata_files: List[MetadataFile] = []
    errors = []
    # 여러 메타데이터를 가진 file 전처리
    for file in files:
        try:
            if file.get_extension() == ".zip":
                metadata_files.extend(extract_zip(file))
            elif file.get_extension() == ".jsonl":
                metadata_files.extend(split_jsonl(file))
            else:
                metadata_files.append(file)
        except ValueError as e:
            errors.append({"filename": file.filename, "error": str(e)})
            continue

    results = []
    for metadata_file in metadata_files:
        try:
            results.append(process_metadata_file(metadata_file))
        except ValueError as e:
            errors.append({"filename": metadata_file.filename, "error": str(e)})
            continue
    return results, errors
