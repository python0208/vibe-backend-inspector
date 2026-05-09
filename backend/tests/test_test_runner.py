import httpx
import sqlite3
from fastapi.testclient import TestClient

from app.main import app
from app.services.openapi_service import FetchedOpenApiDocument, OpenApiService


def create_project(
    client: TestClient,
    database_type: str = "none",
    database_config: dict | None = None,
) -> int:
    response = client.post(
        "/api/projects",
        json={
            "name": "Test Runner Demo",
            "project_path": "D:/demo",
            "service_base_url": "http://example.test",
            "openapi_url": "http://example.test/openapi.json",
            "database_type": database_type,
            "database_config": database_config or {},
            "auth_config": {"type": "none"},
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def sample_openapi_document() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Runner API", "version": "1.0.0"},
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/api/users/{id}": {
                "get": {
                    "summary": "Get user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "verbose",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "boolean"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
    }


def discover_endpoints(client: TestClient, monkeypatch) -> list[dict]:
    async def fake_fetch_document(self: OpenApiService, url: str):
        return (
            FetchedOpenApiDocument(
                url=url,
                payload=sample_openapi_document(),
                detected_format="openapi",
            ),
            None,
        )

    monkeypatch.setattr(OpenApiService, "fetch_document", fake_fetch_document)
    project_id = create_project(client)
    response = client.post(f"/api/projects/{project_id}/openapi/discover")
    assert response.status_code == 200
    endpoints_response = client.get(f"/api/projects/{project_id}/endpoints")
    assert endpoints_response.status_code == 200
    return endpoints_response.json()


class FakeResponse:
    status_code = 200
    headers = {"content-type": "application/json", "set-cookie": "secret"}
    text = '{"ok": true}'

    def json(self) -> dict:
        return {"ok": True}


class FakeAsyncClient:
    last_request: dict | None = None
    on_request = None

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def request(self, method: str, url: str, **kwargs):
        FakeAsyncClient.last_request = {"method": method, "url": url, **kwargs}
        if FakeAsyncClient.on_request:
            FakeAsyncClient.on_request()
        return FakeResponse()


class FailingAsyncClient(FakeAsyncClient):
    async def request(self, method: str, url: str, **kwargs):
        request = httpx.Request(method, url)
        raise httpx.ConnectError("Unable to connect", request=request)


def test_run_endpoint_success_updates_endpoint(monkeypatch) -> None:
    client = TestClient(app)
    endpoints = discover_endpoints(client, monkeypatch)
    endpoint = next(item for item in endpoints if item["path"] == "/api/users/{id}")
    project_id = endpoint["project_id"]
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    response = client.post(
        f"/api/projects/{project_id}/endpoints/{endpoint['id']}/test",
        json={
            "path_params": {"id": "user 1"},
            "query_params": {"verbose": True},
            "headers": {"X-Debug": "1"},
            "bearer_token": "secret-token",
            "json_body": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "passed"
    assert payload["http_status"] == 200
    assert payload["response_body"] == {"ok": True}
    assert payload["db_changes"]["status"] == "skipped"
    assert payload["request_headers"]["Authorization"] == "********"
    assert payload["response_headers"]["set-cookie"] == "********"
    assert FakeAsyncClient.last_request is not None
    assert FakeAsyncClient.last_request["url"] == "http://example.test/api/users/user%201"
    assert FakeAsyncClient.last_request["params"] == {"verbose": True}

    endpoint_response = client.get(f"/api/projects/{project_id}/endpoints/{endpoint['id']}")
    assert endpoint_response.status_code == 200
    updated_endpoint = endpoint_response.json()
    assert updated_endpoint["test_status"] == "passed"
    assert updated_endpoint["last_status_code"] == 200
    assert isinstance(updated_endpoint["last_response_time_ms"], int)

    runs_response = client.get(f"/api/projects/{project_id}/test-runs")
    assert runs_response.status_code == 200
    assert runs_response.json()[0]["id"] == payload["id"]

    detail_response = client.get(f"/api/projects/{project_id}/test-runs/{payload['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == payload["id"]
    client.delete(f"/api/projects/{project_id}")
    FakeAsyncClient.on_request = None


def test_run_endpoint_missing_path_param_returns_422(monkeypatch) -> None:
    client = TestClient(app)
    endpoints = discover_endpoints(client, monkeypatch)
    endpoint = next(item for item in endpoints if item["path"] == "/api/users/{id}")

    response = client.post(
        f"/api/projects/{endpoint['project_id']}/endpoints/{endpoint['id']}/test",
        json={"path_params": {}, "query_params": {}, "headers": {}, "json_body": None},
    )

    assert response.status_code == 422
    assert "Missing path params" in response.text
    client.delete(f"/api/projects/{endpoint['project_id']}")


def test_run_endpoint_request_error_saved_as_failed(monkeypatch) -> None:
    client = TestClient(app)
    endpoints = discover_endpoints(client, monkeypatch)
    endpoint = next(item for item in endpoints if item["path"] == "/health")
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FailingAsyncClient)
    response = client.post(
        f"/api/projects/{endpoint['project_id']}/endpoints/{endpoint['id']}/test",
        json={"path_params": {}, "query_params": {}, "headers": {}, "json_body": None},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["http_status"] is None
    assert response.json()["error_message"] == "Request failed: ConnectError."
    client.delete(f"/api/projects/{endpoint['project_id']}")


def test_run_endpoint_not_found() -> None:
    client = TestClient(app)
    project_id = create_project(client)

    response = client.post(
        f"/api/projects/{project_id}/endpoints/999999/test",
        json={"path_params": {}, "query_params": {}, "headers": {}, "json_body": None},
    )

    assert response.status_code == 404
    client.delete(f"/api/projects/{project_id}")


def test_run_endpoint_captures_sqlite_row_count_diff(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "changes.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password TEXT)")
        connection.execute("INSERT INTO users (email, password) VALUES ('before@example.com', 'secret')")

    client = TestClient(app)
    project_id = create_project(client, "sqlite", {"database_path": str(database_path)})
    async def fake_fetch_document(self: OpenApiService, url: str):
        return (
            FetchedOpenApiDocument(
                url=url,
                payload=sample_openapi_document(),
                detected_format="openapi",
            ),
            None,
        )

    monkeypatch.setattr(OpenApiService, "fetch_document", fake_fetch_document)
    client.post(f"/api/projects/{project_id}/openapi/discover")
    endpoints = client.get(f"/api/projects/{project_id}/endpoints").json()
    endpoint = next(item for item in endpoints if item["path"] == "/health")

    def insert_user() -> None:
        with sqlite3.connect(database_path) as connection:
            connection.execute("INSERT INTO users (email, password) VALUES ('after@example.com', 'new-secret')")

    FakeAsyncClient.on_request = insert_user
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    response = client.post(
        f"/api/projects/{project_id}/endpoints/{endpoint['id']}/test",
        json={"path_params": {}, "query_params": {}, "headers": {}, "json_body": None},
    )

    assert response.status_code == 200
    db_changes = response.json()["db_changes"]
    assert db_changes["status"] == "captured"
    assert db_changes["changed"] is True
    assert db_changes["row_count_diff"]["users"] == {"before": 1, "after": 2, "diff": 1}
    assert "users" in db_changes["tables_modified"]
    assert db_changes["sample_diff"]["users"]["after"][0]["password"] == "********"

    runs_response = client.get(f"/api/projects/{project_id}/test-runs")
    assert runs_response.status_code == 200
    assert runs_response.json()[0]["db_changes"]["changed"] is True
    client.delete(f"/api/projects/{project_id}")
    FakeAsyncClient.on_request = None


def test_run_endpoint_captures_sqlite_schema_diff(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "schema.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")

    client = TestClient(app)
    project_id = create_project(client, "sqlite", {"database_path": str(database_path)})

    async def fake_fetch_document(self: OpenApiService, url: str):
        return (
            FetchedOpenApiDocument(
                url=url,
                payload=sample_openapi_document(),
                detected_format="openapi",
            ),
            None,
        )

    monkeypatch.setattr(OpenApiService, "fetch_document", fake_fetch_document)
    client.post(f"/api/projects/{project_id}/openapi/discover")
    endpoint = next(item for item in client.get(f"/api/projects/{project_id}/endpoints").json() if item["path"] == "/health")

    def alter_table() -> None:
        with sqlite3.connect(database_path) as connection:
            connection.execute("ALTER TABLE users ADD COLUMN display_name TEXT")

    FakeAsyncClient.on_request = alter_table
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)
    response = client.post(
        f"/api/projects/{project_id}/endpoints/{endpoint['id']}/test",
        json={"path_params": {}, "query_params": {}, "headers": {}, "json_body": None},
    )

    assert response.status_code == 200
    schema_diff = response.json()["db_changes"]["schema_diff"]
    assert schema_diff["users"]["columns_added"] == ["display_name"]
    client.delete(f"/api/projects/{project_id}")
    FakeAsyncClient.on_request = None


def test_run_endpoint_db_snapshot_failure_does_not_block_http(monkeypatch, tmp_path) -> None:
    missing_path = tmp_path / "missing.db"
    client = TestClient(app)
    project_id = create_project(client, "sqlite", {"database_path": str(missing_path)})

    async def fake_fetch_document(self: OpenApiService, url: str):
        return (
            FetchedOpenApiDocument(
                url=url,
                payload=sample_openapi_document(),
                detected_format="openapi",
            ),
            None,
        )

    monkeypatch.setattr(OpenApiService, "fetch_document", fake_fetch_document)
    client.post(f"/api/projects/{project_id}/openapi/discover")
    endpoint = next(item for item in client.get(f"/api/projects/{project_id}/endpoints").json() if item["path"] == "/health")
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    response = client.post(
        f"/api/projects/{project_id}/endpoints/{endpoint['id']}/test",
        json={"path_params": {}, "query_params": {}, "headers": {}, "json_body": None},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "passed"
    assert payload["db_changes"]["status"] == "error"
    assert "does not exist" in payload["db_changes"]["warning_message"]
    client.delete(f"/api/projects/{project_id}")
    FakeAsyncClient.on_request = None
