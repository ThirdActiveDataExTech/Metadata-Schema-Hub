import pytest

from app.exceptions.service import InvalidItemStock
from app.schemas.items import CreateItemsRequestModel


def test_create_items_request_model_invalid_data():
    """실패 케이스: 유효하지 않은 아이템 옵션"""
    with pytest.raises(InvalidItemStock):
        CreateItemsRequestModel(name="Alice", status="in stock", stock=-1)


def test_create_items_request_model_default_value():
    """기본값 테스트"""
    item = CreateItemsRequestModel(status="in stock", stock=10)
    assert item.name == "no name"
