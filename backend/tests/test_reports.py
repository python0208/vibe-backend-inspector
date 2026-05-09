import sqlite3

from fastapi.testclient import TestClient

from app.main import app
from app.services.openapi_service import FetchedOpenApiDocument, OpenApiService


def create_project(client: TestClient, database_type: str = "none", database_config: dict | None = None) -> int:
    response = client.post(
        "/api/projects",
        json={
            "name": "Reports Demo",
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
        "info": {"title": "Reports API", "version": "1.0.0"},
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/api/users": {
                "post": {
                    "summary": "Create user",
                    "responses": {"201": {"description": "Created"}},
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
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
    }


def discover_endpoints(client: TestClient, project_id: int, monkeypatch) -> list[dict]:
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
    response = client.post(f"/api/projects/{project_id}/openapi/discover")
    assert response.status_code == 200
    endpoints_response = client.get(f"/api/projects/{project_id}/endpoints")
    assert endpoints_response.status_code == 200
    return endpoints_response.json()


class OkResponse:
    status_code = 200
    headers = {"content-type": "application/json"}
    text = '{"ok": true}'

    def json(self) -> dict:
        return {"ok": True}


class ServerErrorResponse:
    status_code = 500
    headers = {"content-type": "application/json"}
    text = '{"error": "boom"}'

    def json(self) -> dict:
        return {"error": "boom"}


class ValidationErrorResponse:
    status_code = 422
    headers = {"content-type": "application/json"}
    text = '{"detail": [{"loc": ["body", "name"], "msg": "Field required"}]}'

    def json(self) -> dict:
        return {"detail": [{"loc": ["body", "name"], "msg": "Field required"}]}


class FakeAsyncClient:
    response = OkResponse()
    on_request = None

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def request(self, method: str, url: str, **kwargs):
        if FakeAsyncClient.on_request:
            FakeAsyncClient.on_request()
        return FakeAsyncClient.response


def create_mock_llm_config(client: TestClient) -> int:
    response = client.post(
        "/api/llm/configs",
        json={
            "provider": "mock",
            "display_name": "Report Mock",
            "base_url": "mock://local",
            "api_key": "secret-key",
            "model_name": "mock",
            "temperature": 0.2,
            "timeout_seconds": 30,
            "max_tokens": 2000,
            "enabled": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_report_summary_empty_state() -> None:
    client = TestClient(app)
    project_id = create_project(client)

    response = client.get(f"/api/projects/{project_id}/reports/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["endpoint_summary"]["total"] == 0
    assert payload["test_summary"]["total_runs"] == 0
    assert payload["overall_score"] == 0
    assert payload["risk_level"] == "high"
    client.delete(f"/api/projects/{project_id}")


def test_report_generate_latest_and_markdown_include_real_test_data(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "reports.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
        connection.execute("INSERT INTO users (email) VALUES ('before@example.com')")

    client = TestClient(app)
    project_id = create_project(client, "sqlite", {"database_path": str(database_path)})
    endpoints = discover_endpoints(client, project_id, monkeypatch)
    health = next(item for item in endpoints if item["path"] == "/health")
    create_user = next(item for item in endpoints if item["path"] == "/api/users")
    get_user = next(item for item in endpoints if item["path"] == "/api/users/{id}")
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    FakeAsyncClient.response = OkResponse()
    FakeAsyncClient.on_request = None
    response = client.post(
        f"/api/projects/{project_id}/endpoints/{health['id']}/test",
        json={"path_params": {}, "query_params": {}, "headers": {}, "json_body": None},
    )
    assert response.status_code == 200

    def insert_user() -> None:
        with sqlite3.connect(database_path) as connection:
            connection.execute("INSERT INTO users (email) VALUES ('after@example.com')")

    FakeAsyncClient.response = OkResponse()
    FakeAsyncClient.on_request = insert_user
    response = client.post(
        f"/api/projects/{project_id}/endpoints/{create_user['id']}/test",
        json={"path_params": {}, "query_params": {}, "headers": {}, "json_body": {"email": "after@example.com"}},
    )
    assert response.status_code == 200

    FakeAsyncClient.response = ValidationErrorResponse()
    FakeAsyncClient.on_request = None
    response = client.post(
        f"/api/projects/{project_id}/endpoints/{get_user['id']}/test",
        json={"path_params": {"id": 1}, "query_params": {}, "headers": {}, "json_body": None},
    )
    assert response.status_code == 200

    summary_response = client.get(f"/api/projects/{project_id}/reports/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["endpoint_summary"]["total"] == 3
    assert summary["endpoint_summary"]["tested"] == 3
    assert summary["test_summary"]["validation_error_count"] == 1
    assert summary["database_change_summary"]["tests_with_db_changes"] == 1
    assert summary["database_change_summary"]["row_count_diff"]["users"]["diff"] == 1

    generate_response = client.post(f"/api/projects/{project_id}/reports/generate")
    assert generate_response.status_code == 200
    report = generate_response.json()
    assert report["id"]
    assert report["markdown_content"].startswith("# Reports Demo Acceptance Report")
    assert "422 validation errors: 1" in report["markdown_content"]

    latest_response = client.get(f"/api/projects/{project_id}/reports/latest")
    assert latest_response.status_code == 200
    assert latest_response.json()["report"]["id"] == report["id"]

    markdown_response = client.get(f"/api/projects/{project_id}/reports/{report['id']}/markdown")
    assert markdown_response.status_code == 200
    assert "text/markdown" in markdown_response.headers["content-type"]
    assert "## Database Changes" in markdown_response.text

    client.delete(f"/api/projects/{project_id}")
    FakeAsyncClient.response = OkResponse()
    FakeAsyncClient.on_request = None


def test_report_summary_includes_ai_smart_test_results(monkeypatch) -> None:
    client = TestClient(app)
    project_id = create_project(client)
    endpoints = discover_endpoints(client, project_id, monkeypatch)
    config_id = create_mock_llm_config(client)
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    plan_response = client.post(
        f"/api/projects/{project_id}/ai-tests/plans",
        json={
            "llm_config_id": config_id,
            "endpoint_ids": [endpoints[0]["id"]],
            "scope": "single_endpoint",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()["plan"]
    step_id = plan["steps"][0]["step_id"]

    FakeAsyncClient.response = OkResponse()
    execute_response = client.post(
        f"/api/projects/{project_id}/ai-tests/plans/{plan['plan_id']}/execute-step/{step_id}",
        json={"confirmed": False},
    )
    assert execute_response.status_code == 200
    analysis_response = client.post(f"/api/projects/{project_id}/ai-tests/plans/{plan['plan_id']}/analyze")
    assert analysis_response.status_code == 200

    summary_response = client.get(f"/api/projects/{project_id}/reports/summary")
    assert summary_response.status_code == 200
    ai_summary = summary_response.json()["ai_test_summary"]
    assert ai_summary["plan_count"] == 1
    assert ai_summary["steps_total"] == 1
    assert ai_summary["steps_passed"] == 1
    assert ai_summary["analysis_summary"]

    client.delete(f"/api/projects/{project_id}")
    client.delete(f"/api/llm/configs/{config_id}")
    FakeAsyncClient.response = OkResponse()
    FakeAsyncClient.on_request = None
