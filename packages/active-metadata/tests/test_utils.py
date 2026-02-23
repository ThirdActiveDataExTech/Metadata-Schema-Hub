"""Unit tests for utility functions."""

import pandas as pd

from active_metadata.utils import to_str_list


def test_to_str_list_with_string():
    """Test with plain string."""
    assert to_str_list("test") == ["test"]


def test_to_str_list_with_comma_separated():
    """Test with comma-separated string."""
    assert to_str_list("a, b, c") == ["a", "b", "c"]
    assert to_str_list("a,b,c") == ["a", "b", "c"]


def test_to_str_list_with_list():
    """Test with list input."""
    assert to_str_list(["x", "y", "z"]) == ["x", "y", "z"]
    assert to_str_list([1, "y", "z"]) == ["1", "y", "z"]


def test_to_str_list_with_empty():
    """Test with empty input."""
    assert to_str_list("") == []
    assert to_str_list([]) == []
    assert to_str_list(None) == []


def test_to_str_list_with_pandas_series_single():
    """Test with single-value pandas Series."""
    series = pd.Series(["value"])
    assert to_str_list(series) == ["value"]


def test_to_str_list_with_pandas_series_multiple():
    """Test with multi-value pandas Series."""
    series = pd.Series(["a", "b", "c"])
    result = to_str_list(series)
    assert len(result) == 3
    assert result == ["a", "b", "c"]


def test_to_str_list_with_mixed_types():
    """Test with mixed data types in pandas Series."""
    series = pd.Series([1, "text", 3.14])
    result = to_str_list(series)
    assert len(result) == 3
    assert result == ["1", "text", "3.14"]
