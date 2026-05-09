from fastapi.testclient import TestClient

from app.main import app
from app.services.openapi_service import FetchedOpenApiDocument, OpenApiService


def create_project(client: TestClient) -> int:
    response = client.post(
        "/api/projects",
        json={
            "name": "AI Test Demo",
            "project_path": "D:/demo",
            "service_base_url": "http://example.test",
            "openapi_url": "http://example.test/openapi.json",
            "database_type": "none",
            "database_config": {},
            "auth_config": {"type": "none"},
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def sample_openapi_document() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "AI Runner API", "version": "1.0.0"},
        "paths": {
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


def create_mock_llm_config(client: TestClient) -> int:
    response = client.post(
        "/api/llm/configs",
        json={
            "provider": "mock",
            "display_name": "Mock",
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
    payload = response.json()
    assert payload["masked_api_key"] == "********"
    assert "secret-key" not in str(payload)
    return payload["id"]


class FakeResponse:
    status_code = 200
    headers = {"content-type": "application/json"}
    text = '{"ok": true}'

    def json(self) -> dict:
        return {"ok": True}


class FakeAsyncClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def request(self, method: str, url: str, **kwargs):
        return FakeResponse()


def test_llm_config_crud_masks_api_key() -> None:
    client = TestClient(app)
    config_id = create_mock_llm_config(client)

    list_response = client.get("/api/llm/configs")
    assert list_response.status_code == 200
    assert "secret-key" not in str(list_response.json())

    test_response = client.post(f"/api/llm/configs/{config_id}/test")
    assert test_response.status_code == 200
    assert test_response.json()["ok"] is True

    update_response = client.put(
        f"/api/llm/configs/{config_id}",
        json={"display_name": "Updated Mock", "api_key": "********"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["display_name"] == "Updated Mock"
    assert update_response.json()["masked_api_key"] == "********"

    delete_response = client.delete(f"/api/llm/configs/{config_id}")
    assert delete_response.status_code == 204


def test_ai_plan_generation_and_step_execution_reuses_test_service(monkeypatch) -> None:
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
    monkeypatch.setattr("app.services.test_service.httpx.AsyncClient", FakeAsyncClient)

    client = TestClient(app)
    project_id = create_project(client)
    config_id = create_mock_llm_config(client)
    discover_response = client.post(f"/api/projects/{project_id}/openapi/discover")
    assert discover_response.status_code == 200
    endpoints = client.get(f"/api/projects/{project_id}/endpoints").json()
    endpoint = endpoints[0]

    plan_response = client.post(
        f"/api/projects/{project_id}/ai-tests/plans",
        json={
            "llm_config_id": config_id,
            "endpoint_ids": [endpoint["id"]],
            "scope": "single_endpoint",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()["plan"]
    assert plan["steps"][0]["endpoint_id"] == endpoint["id"]
    assert plan["steps"][0]["status"] == "pending"

    step_id = plan["steps"][0]["step_id"]
    execute_response = client.post(
        f"/api/projects/{project_id}/ai-tests/plans/{plan['plan_id']}/execute-step/{step_id}",
        json={"confirmed": False},
    )
    assert execute_response.status_code == 200
    payload = execute_response.json()
    assert payload["ok"] is True
    assert payload["test_run"]["status"] == "passed"
    assert payload["test_run"]["db_changes"]["status"] == "skipped"

    analysis_response = client.post(f"/api/projects/{project_id}/ai-tests/plans/{plan['plan_id']}/analyze")
    assert analysis_response.status_code == 200
    assert analysis_response.json()["analysis"]

    client.delete(f"/api/projects/{project_id}")
    client.delete(f"/api/llm/configs/{config_id}")


def test_ai_plan_generation_accepts_wrapped_deepseek_style_json(monkeypatch) -> None:
    async def fake_fetch_document(self: OpenApiService, url: str):
        return (
            FetchedOpenApiDocument(
                url=url,
                payload=sample_openapi_document(),
                detected_format="openapi",
            ),
            None,
        )

    async def fake_chat_json(self, config, messages, json_schema):
        return {
            "test_plan": {
                "test_cases": [
                    {
                        "name": "Fetch an existing user",
                        "method": "GET",
                        "path": "/api/users/{id}",
                        "path_parameters": {"id": 1},
                        "query_parameters": {},
                        "expected_status_code": 200,
                        "expected_result": "The API should return a user object.",
                    }
                ]
            }
        }

    monkeypatch.setattr(OpenApiService, "fetch_document", fake_fetch_document)
    monkeypatch.setattr("app.services.ai_test_service.LLMService.chat_json", fake_chat_json)

    client = TestClient(app)
    project_id = create_project(client)
    config_id = create_mock_llm_config(client)
    client.post(f"/api/projects/{project_id}/openapi/discover")
    endpoint = client.get(f"/api/projects/{project_id}/endpoints").json()[0]

    response = client.post(
        f"/api/projects/{project_id}/ai-tests/plans",
        json={
            "llm_config_id": config_id,
            "endpoint_ids": [endpoint["id"]],
            "scope": "single_endpoint",
        },
    )

    assert response.status_code == 200
    plan = response.json()["plan"]
    assert plan["summary"] == "AI-generated API test plan."
    assert plan["risk_level"] == "low"
    assert plan["steps"][0]["path_params"] == {"id": 1}
    assert plan["steps"][0]["expected_status"] == 200

    client.delete(f"/api/projects/{project_id}")
    client.delete(f"/api/llm/configs/{config_id}")


def test_ai_plan_generation_falls_back_when_model_returns_no_steps(monkeypatch) -> None:
    async def fake_fetch_document(self: OpenApiService, url: str):
        return (
            FetchedOpenApiDocument(
                url=url,
                payload=sample_openapi_document(),
                detected_format="openapi",
            ),
            None,
        )

    async def fake_chat_json(self, config, messages, json_schema):
        return {"test_plan": {"summary": "No executable cases here", "risk_level": "low"}}

    monkeypatch.setattr(OpenApiService, "fetch_document", fake_fetch_document)
    monkeypatch.setattr("app.services.ai_test_service.LLMService.chat_json", fake_chat_json)

    client = TestClient(app)
    project_id = create_project(client)
    config_id = create_mock_llm_config(client)
    client.post(f"/api/projects/{project_id}/openapi/discover")
    endpoint = client.get(f"/api/projects/{project_id}/endpoints").json()[0]

    response = client.post(
        f"/api/projects/{project_id}/ai-tests/plans",
        json={
            "llm_config_id": config_id,
            "endpoint_ids": [endpoint["id"]],
            "scope": "single_endpoint",
        },
    )

    assert response.status_code == 200
    step = response.json()["plan"]["steps"][0]
    assert step["endpoint_id"] == endpoint["id"]
    assert "fallback-step" in step["step_id"]
    assert "fallback" in step["reasoning"].lower()

    client.delete(f"/api/projects/{project_id}")
    client.delete(f"/api/llm/configs/{config_id}")
