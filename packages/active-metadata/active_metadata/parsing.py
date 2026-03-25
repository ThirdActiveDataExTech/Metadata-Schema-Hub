"""Field parsing utilities for metadata models.

Provides type conversion functions for catalog entry fields.
Used by DTOs and services to normalize incoming data.
"""

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

__all__ = ["parse_date", "to_str_list", "to_atomic_list", "convert_field_types", "detect_extension"]

# Supported separators for list parsing
LIST_SEPARATORS = [",", ";", "/", "|", "@"]


def parse_date(value: Any) -> date | None:
    """Parse date from various string formats.

    Supported formats:
        - ISO 8601: 2024-01-15, 2024/01/15
        - European: 15-01-2024, 15/01/2024
        - Compact: 20240115
        - ISO with time: 2024-01-15T10:30:00Z

    Args:
        value: Date value (date, str, or None)

    Returns:
        Parsed date or None if unparseable
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value

    value_str = str(value).strip()
    if not value_str:
        return None

    # Try common date formats
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(value_str, fmt).date()
        except ValueError:
            continue

    # Try ISO format with time
    try:
        return datetime.fromisoformat(value_str.replace("Z", "+00:00")).date()
    except ValueError:
        pass

    logging.warning(f"Could not parse date: {value_str}")
    return None


def to_str_list(value: Any) -> list[str]:
    """Convert various data types to string list.

    Handles:
        - None/empty -> []
        - list -> list[str] (filtered empty values)
        - str with separators (,;/|) -> split list
        - str without separators -> single-element list
        - other types -> [str(value)]

    Args:
        value: Data to convert (string, list, etc.)

    Returns:
        Converted string list (empty list if no valid values)
    """
    # Empty value handling
    if not value:
        return []

    # List handling
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    # String handling
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []

        # Try separators
        for sep in LIST_SEPARATORS:
            if sep in value:
                return [item.strip() for item in value.split(sep) if item.strip()]

        return [value]

    # Other type handling
    try:
        str_value = str(value).strip()
        return [str_value] if str_value else []
    except Exception as e:
        logging.error(f"String list conversion error: {e}")
        return []


def to_atomic_list(value: Any) -> list[str]:
    """Convert value to string list without separator splitting.

    Unlike to_str_list, treats each value as a single atomic entry.
    URLs and other separator-containing strings are preserved intact.

    Returns:
        list[str] (empty list if no valid values)
    """
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    stripped = str(value).strip()
    return [stripped] if stripped else []


def convert_field_types(
    mapped_fields: dict[str, Any],
    list_fields: set[str] | list[str],
    date_fields: set[str] | list[str],
    atomic_list_fields: set[str] | list[str] | None = None,
) -> dict[str, Any]:
    """Convert field values to their expected types.

    Args:
        mapped_fields: Raw field values
        list_fields: Field names that should be list[str] (separator-split)
        date_fields: Field names that should be date
        atomic_list_fields: Field names that are list[str] but each value is atomic (no split)

    Returns:
        Dict with converted field values
    """
    list_fields_set = set(list_fields)
    date_fields_set = set(date_fields)
    atomic_list_fields_set = set(atomic_list_fields) if atomic_list_fields else set()

    result = {}
    for field, value in mapped_fields.items():
        if field in date_fields_set:
            result[field] = parse_date(value)
        elif field in list_fields_set:
            parsed = to_str_list(value)
            result[field] = parsed if parsed else None  # [] -> None for DB nullable
        elif field in atomic_list_fields_set:
            result[field] = to_atomic_list(value)
        else:
            result[field] = value
    return result


def detect_extension(payload: str | bytes, filename: str | None) -> str:
    """Detect file extension from filename or content.

    Args:
        payload: File content
        filename: Original filename (optional)

    Returns:
        Detected extension (xml, json, or bin)
    """
    if filename:
        ext = Path(filename).suffix.lstrip(".")
        if ext:
            return ext

    # Content-based detection
    if isinstance(payload, str):
        content = payload.strip()
    else:
        try:
            content = payload.decode("utf-8").strip()
        except Exception:
            return "bin"

    if content.startswith("<?xml") or content.startswith("<rdf:RDF"):
        return "xml"
    elif content.startswith("{") or content.startswith("["):
        return "json"

    return "bin"
