from fastapi.testclient import TestClient

from app.config import settings
from app.exceptions.service import InvalidItemStock, ItemNotFoundError
from app.main import app
from tests.check_common_conditions import check_success_common_conditions, check_failed_common_conditions

client = TestClient(app)


def test_read_items():
    response = client.get("/items", headers={"x-token": settings.X_TOKEN})
    check_success_common_conditions(response)
    response_json = response.json()
    assert response_json['result']['plumbus']['name'] == 'Plumbus'
    assert response_json['result']['gun']['name'] == 'Portal Gun'


def test_read_item():
    item_id = "gun"
    response = client.get(f"/items/{item_id}", headers={"x-token": settings.X_TOKEN})
    check_success_common_conditions(response)
    response_json = response.json()
    assert response_json['result']['name'] == 'Portal Gun'
    assert response_json['result']['item_id'] == item_id


def test_update_item():
    item_id = "plumbus"
    response = client.put(f"/items/{item_id}", headers={"x-token": settings.X_TOKEN})
    check_success_common_conditions(response)
    response_json = response.json()
    assert response_json['result']['name'] == 'The great Plumbus'
    assert response_json['result']['item_id'] == item_id


def test_create_item(create_item_example):
    response = client.post(url="/items", headers={"x-token": settings.X_TOKEN}, json=create_item_example)
    check_success_common_conditions(response)
    response_json = response.json()
    assert response_json["result"]["item"]["name"] == create_item_example["name"]
    assert response_json["result"]["item"]["status"] == create_item_example["status"]
    assert response_json["result"]["item"]["stock"] == create_item_example["stock"]


def test_read_item_not_found_exception():
    item_id = "non-exist item"
    response = client.get(f"/items/{item_id}", headers={"x-token": settings.X_TOKEN})
    check_failed_common_conditions(response, ItemNotFoundError(item_id))


def test_create_item_lower_than_zero_exception(create_item_lower_than_zero_exception_item_example):
    response = client.post(
        url="/items", headers={"x-token": settings.X_TOKEN}, json=create_item_lower_than_zero_exception_item_example)
    check_failed_common_conditions(response, InvalidItemStock(create_item_lower_than_zero_exception_item_example["stock"]))
