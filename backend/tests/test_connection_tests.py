import sqlite3

from fastapi.testclient import TestClient

from app.main import app


def test_database_connection_sqlite(tmp_path) -> None:
    database_path = tmp_path / "demo.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE demo (id integer primary key)")

    client = TestClient(app)
    response = client.post(
        "/api/connection-tests/database",
        json={"database_type": "sqlite", "database_config": {"database_path": str(database_path)}},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_database_connection_sqlite_missing_path() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/connection-tests/database",
        json={"database_type": "sqlite", "database_config": {}},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_openapi_rejects_non_json() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/connection-tests/openapi",
        json={"url": "http://127.0.0.1:1/openapi.json"},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is False
