import sqlite3

from fastapi.testclient import TestClient

from app.main import app


def create_project(client: TestClient, database_type: str, database_config: dict) -> int:
    response = client.post(
        "/api/projects",
        json={
            "name": "Database Demo",
            "project_path": "D:/demo",
            "service_base_url": "http://localhost:8000",
            "openapi_url": None,
            "database_type": database_type,
            "database_config": database_config,
            "auth_config": {"type": "none"},
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_sqlite_database(database_path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL)")
        connection.execute("INSERT INTO users (email) VALUES ('user@example.com')")


def test_project_database_routes_sqlite(tmp_path) -> None:
    database_path = tmp_path / "route.db"
    create_sqlite_database(database_path)
    client = TestClient(app)
    project_id = create_project(client, "sqlite", {"database_path": str(database_path)})

    connection_response = client.post(f"/api/projects/{project_id}/database/test-connection")
    assert connection_response.status_code == 200
    assert connection_response.json()["ok"] is True

    inspect_response = client.post(f"/api/projects/{project_id}/database/inspect")
    assert inspect_response.status_code == 200
    payload = inspect_response.json()
    assert payload["ok"] is True
    assert payload["schema"]["database_name"] == "route.db"
    assert payload["schema"]["tables"][0]["name"] == "users"
    assert payload["schema"]["tables"][0]["row_count"] == 1

    schema_response = client.get(f"/api/projects/{project_id}/database/schema")
    assert schema_response.status_code == 200
    assert schema_response.json()["ok"] is True

    client.delete(f"/api/projects/{project_id}")


def test_project_database_none_returns_clear_error() -> None:
    client = TestClient(app)
    project_id = create_project(client, "none", {})

    response = client.post(f"/api/projects/{project_id}/database/inspect")

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["message"] == "No database configured."
    client.delete(f"/api/projects/{project_id}")


def test_project_database_not_found() -> None:
    client = TestClient(app)

    response = client.post("/api/projects/999999/database/inspect")

    assert response.status_code == 404
