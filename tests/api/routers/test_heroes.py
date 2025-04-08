"""In-memory SQLite database for testing"""

from app.config import settings


def test_get_heroes(client):
    """미리 셋팅하지 않으면 조회되는 히어로 없음"""
    response = client.get("/heroes/", headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert isinstance(data["result"], list)
    assert len(data["result"]) == 0


def test_create_hero(client):
    response = client.post("/heroes/", json={"name": "Test Hero", "age": 30, "secret_name": "Secret"},
                           headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["name"] == "Test Hero"
    assert data["result"]["age"] == 30
    assert data["result"]["secret_name"] == "Secret"


def test_get_hero(client):
    response = client.post("/heroes/", json={"name": "Test Hero", "age": 30, "secret_name": "Secret"},
                           headers={"x-token": settings.X_TOKEN})
    hero_id = response.json()["result"]["id"]
    response = client.get(f"/heroes/{hero_id}", headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["name"] == "Test Hero"


def test_update_hero(client):
    response = client.post("/heroes/", json={"name": "Test Hero", "age": 30, "secret_name": "Secret"},
                           headers={"x-token": settings.X_TOKEN})
    hero_id = response.json()["result"]["id"]
    response = client.patch(f"/heroes/{hero_id}",
                            json={"name": "Updated Hero", "age": 35, "secret_name": "Updated Secret"},
                            headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["name"] == "Updated Hero"
    assert data["result"]["age"] == 35
    assert data["result"]["secret_name"] == "Updated Secret"


def test_delete_hero(client):
    response = client.post("/heroes/", json={"name": "Test Hero", "age": 30, "secret_name": "Secret"},
                           headers={"x-token": settings.X_TOKEN})
    hero_id = response.json()["result"]["id"]
    response = client.delete(f"/heroes/{hero_id}", headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["name"] == "Test Hero"
    response = client.get(f"/heroes/{hero_id}", headers={"x-token": settings.X_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hero not found"
