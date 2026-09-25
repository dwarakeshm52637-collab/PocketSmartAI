from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json()["status"] == "ok"


def test_home_page():

    response = client.get("/")

    assert response.status_code == 200

    assert "PocketSmart AI" in response.text


def test_login_unknown_user():

    response = client.post(
        "/login",
        json={
            "email": "unknown@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401