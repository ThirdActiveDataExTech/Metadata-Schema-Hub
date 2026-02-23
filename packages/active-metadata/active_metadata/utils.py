"""Utility functions for data transformation."""
import logging
from typing import Any

import pandas as pd

__all__ = ["to_str_list"]


def to_str_list(data: Any) -> list[str]:
    """Convert various data types to string list.

    Handles: strings with separators, lists, pd.Series, etc.

    Args:
        data: Data to convert (string, list, pd.Series, etc.)

    Returns:
        List[str]: Converted string list
    """
    # Series handling (check first to avoid ambiguous truth value error)
    if isinstance(data, pd.Series):
        # Single value or multiple values handling
        if len(data) == 1:
            return to_str_list(data.iloc[0])

        # Convert Series values to list for processing
        data = [v for v in data.values if not pd.isna(v)]
        # Early return for empty list
        if not data:
            return []

    # Empty value handling
    if not data:
        return []

    # List handling
    if isinstance(data, list):
        return [str(item).strip() for item in data if str(item).strip()]

    # String handling
    if isinstance(data, str):
        data = data.strip()
        if not data:
            return []

        # Separator handling
        separators = [",", ";", "/", "|"]
        for sep in separators:
            if sep in data:
                return [item.strip() for item in data.split(sep) if item.strip()]

        return [data]

    # Other type handling
    try:
        str_value = str(data).strip()
        return [str_value] if str_value else []
    except Exception as e:
        logging.error(f"String list conversion error: {e}")
        return []
