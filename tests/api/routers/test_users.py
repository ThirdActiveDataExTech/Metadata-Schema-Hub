from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from tests.check_common_conditions import check_success_common_conditions

client = TestClient(app)


def test_read_users():
    response = client.get("/users", headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    check_success_common_conditions(response)
    response_json = response.json()
    assert isinstance(response_json['result']['users'], list)


def test_read_user_me():
    response = client.get("/users/me", headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    check_success_common_conditions(response)
    response_json = response.json()
    assert response_json['result']['username'] == "fakecurrentuser"


def test_read_user():
    user_name = "sally"
    response = client.get(f"/users/{user_name}", headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    check_success_common_conditions(response)
    response_json = response.json()
    assert response_json['result']['username'] == user_name
