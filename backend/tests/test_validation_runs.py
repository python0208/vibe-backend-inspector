import httpx
from fastapi.testclient import TestClient

from app.main import app


def create_project(client: TestClient) -> int:
    response = client.post(
        "/api/projects",
        json={
            "name": "Validation Demo",
            "project_path": "D:/demo",
            "service_base_url": "http://example.test",
            "openapi_url": None,
            "database_type": "none",
            "database_config": {},
            "auth_config": {"type": "none"},
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_endpoint(client: TestClient, project_id: int, method: str, path: str, schema: dict | None = None) -> dict:
    response = client.post(
        f"/api/projects/{project_id}/endpoints",
        json={
            "method": method,
            "path": path,
            "summary": f"{method} {path}",
            "request_body_schema": schema or {},
            "response_schema": {},
            "auth_required": False,
        },
    )
    assert response.status_code == 201
    return response.json()


class FakeResponse:
    headers = {"content-type": "application/json"}
    text = '{"ok": true}'

    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def json(self) -> dict:
        return {"ok": self.status_code < 400}


class FakeAsyncClient:
    requests: list[dict] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def request(self, method: str, url: str, **kwargs):
        self.requests.append({"method": method, "url": url, **kwargs})
        if url.endswith("/api/fail"):
            return FakeResponse(500)
        if "/api/invalid" in url:
            return FakeResponse(422)
        if url.endswith("/api/auth"):
            return FakeResponse(401)
        if url.endswith("/api/forbidden"):
            return FakeResponse(403)
        if url.endswith("/api/missing"):
            return FakeResponse(404)
        return FakeResponse(200)


class FailingAsyncClient(FakeAsyncClient):
    async def request(self, method: str, url: str, **kwargs):
        if url.endswith("/api/fail"):
            request = httpx.Request(method, url)
            raise httpx.ConnectError("Unable to connect", request=request)
        return await super().request(method, url, **kwargs)


def test_validation_run_executes_batch_and_skips_destructive(monkeypatch) -> None:
    client = TestClient(app)
    project_id = create_project(client)
    get_endpoint = create_endpoint(client, project_id, "GET", "/api/health")
    post_endpoint = create_endpoint(
        client,
        project_id,
        "POST",
        "/api/users",
        {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}},
    )
    delete_endpoint = create_endpoint(client, project_id, "DELETE", "/api/users/{id}")
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    response = client.post(
        f"/api/projects/{project_id}/validation-runs",
        json={
            "name": "Smoke validation",
            "skip_destructive": True,
            "include_get": True,
            "include_post": True,
            "include_put_patch_delete": True,
        },
    )

    assert response.status_code == 201
    run = response.json()
    assert run["status"] == "completed"
    assert run["total_count"] == 3
    assert run["passed_count"] == 2
    assert run["skipped_count"] == 1
    assert run["summary"]["pass_rate"] == 66.7
    items = run["items"]
    assert {item["endpoint_id"] for item in items} == {
        get_endpoint["id"],
        post_endpoint["id"],
        delete_endpoint["id"],
    }
    skipped = next(item for item in items if item["method"] == "DELETE")
    assert skipped["status"] == "skipped"
    assert "destructive" in skipped["error_message"].lower()
    assert all(item["test_run_id"] for item in items if item["status"] == "passed")

    detail_response = client.get(f"/api/projects/{project_id}/validation-runs/{run['id']}")
    assert detail_response.status_code == 200
    assert len(detail_response.json()["items"]) == 3

    list_response = client.get(f"/api/projects/{project_id}/validation-runs")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == run["id"]

    client.delete(f"/api/projects/{project_id}")


def test_validation_run_single_failure_does_not_stop_batch(monkeypatch) -> None:
    client = TestClient(app)
    project_id = create_project(client)
    create_endpoint(client, project_id, "GET", "/api/fail")
    create_endpoint(client, project_id, "GET", "/api/health")
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FailingAsyncClient)

    response = client.post(
        f"/api/projects/{project_id}/validation-runs",
        json={"name": "Failure validation", "include_get": True, "include_post": False},
    )

    assert response.status_code == 201
    run = response.json()
    assert run["total_count"] == 2
    assert run["passed_count"] == 1
    assert run["failed_count"] == 1
    assert {item["status"] for item in run["items"]} == {"passed", "failed"}

    client.delete(f"/api/projects/{project_id}")


def test_validation_run_selected_methods_and_report_summary(monkeypatch) -> None:
    client = TestClient(app)
    project_id = create_project(client)
    selected = create_endpoint(client, project_id, "GET", "/api/selected")
    create_endpoint(client, project_id, "POST", "/api/users")
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    response = client.post(
        f"/api/projects/{project_id}/validation-runs",
        json={
            "name": "Selected validation",
            "endpoint_ids": [selected["id"]],
            "methods": ["GET"],
            "include_post": False,
        },
    )
    assert response.status_code == 201
    assert response.json()["total_count"] == 1
    assert response.json()["items"][0]["endpoint_id"] == selected["id"]

    summary_response = client.get(f"/api/projects/{project_id}/reports/summary")
    assert summary_response.status_code == 200
    validation_summary = summary_response.json()["validation_run_summary"]
    assert validation_summary["latest_run_id"] == response.json()["id"]
    assert validation_summary["passed_count"] == 1

    report_response = client.post(f"/api/projects/{project_id}/reports/generate")
    assert report_response.status_code == 200
    assert "Validation Run Summary" in report_response.json()["markdown_content"]

    client.delete(f"/api/projects/{project_id}")


def test_validation_run_item_exposes_generated_request_and_failure_category(monkeypatch) -> None:
    client = TestClient(app)
    project_id = create_project(client)
    response = client.post(
        f"/api/projects/{project_id}/endpoints",
        json={
            "method": "GET",
            "path": "/api/invalid/{id}",
            "summary": "Invalid request",
            "query_params": [
                {
                    "name": "email",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"},
                }
            ],
            "path_params": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                }
            ],
            "request_body_schema": {},
            "response_schema": {},
            "auth_required": False,
        },
    )
    assert response.status_code == 201
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    run_response = client.post(
        f"/api/projects/{project_id}/validation-runs",
        json={"name": "Explain validation", "include_get": True, "include_post": False},
    )

    assert run_response.status_code == 201
    item = run_response.json()["items"][0]
    assert item["status"] == "failed"
    assert item["http_status"] == 422
    assert item["failure_category"] == "validation_error"
    assert item["request_path_params"] == {"id": 1}
    assert item["request_query_params"] == {"email": "test@example.com"}
    assert item["request_headers"] == {}
    assert item["response_body_summary"] == {"ok": False}
    assert item["suggestion"]

    client.delete(f"/api/projects/{project_id}")


def test_validation_run_failure_categories_for_common_statuses(monkeypatch) -> None:
    client = TestClient(app)
    project_id = create_project(client)
    create_endpoint(client, project_id, "GET", "/api/auth")
    create_endpoint(client, project_id, "GET", "/api/forbidden")
    create_endpoint(client, project_id, "GET", "/api/missing")
    create_endpoint(client, project_id, "GET", "/api/fail")
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    response = client.post(
        f"/api/projects/{project_id}/validation-runs",
        json={"name": "Status categories", "include_get": True, "include_post": False},
    )

    assert response.status_code == 201
    categories = {item["path"]: item["failure_category"] for item in response.json()["items"]}
    assert categories["/api/auth"] == "auth_required"
    assert categories["/api/forbidden"] == "permission_denied"
    assert categories["/api/missing"] == "not_found"
    assert categories["/api/fail"] == "server_error"

    client.delete(f"/api/projects/{project_id}")


def test_validation_run_skipped_categories_include_suggestions() -> None:
    client = TestClient(app)
    project_id = create_project(client)
    create_endpoint(client, project_id, "DELETE", "/api/users/{id}")
    create_endpoint(client, project_id, "POST", "/api/manual-users")

    response = client.post(
        f"/api/projects/{project_id}/validation-runs",
        json={
            "name": "Skipped categories",
            "include_get": True,
            "include_post": True,
            "include_put_patch_delete": True,
            "skip_destructive": True,
        },
    )

    assert response.status_code == 201
    categories = {item["path"]: item for item in response.json()["items"]}
    assert categories["/api/users/{id}"]["failure_category"] == "skipped_safety"
    assert categories["/api/users/{id}"]["request_path_params"] == {"id": 1}
    assert categories["/api/manual-users"]["failure_category"] == "needs_user_input"
    assert categories["/api/manual-users"]["suggestion"]

    client.delete(f"/api/projects/{project_id}")
