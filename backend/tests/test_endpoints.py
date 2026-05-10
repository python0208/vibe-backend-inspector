import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.openapi_service import FetchedOpenApiDocument, OpenApiService


def create_project(client: TestClient) -> int:
    response = client.post(
        "/api/projects",
        json={
            "name": "Endpoint Demo",
            "project_path": "D:/demo",
            "service_base_url": "http://localhost:8000",
            "openapi_url": "http://localhost:8000/openapi.json",
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
        "info": {"title": "Demo API", "version": "1.0.0"},
        "paths": {
            "/api/users": {
                "get": {
                    "summary": "List users",
                    "operationId": "listUsers",
                    "responses": {"200": {"description": "OK"}},
                },
                "post": {
                    "summary": "Create user",
                    "operationId": "createUser",
                    "responses": {"201": {"description": "Created"}},
                },
            }
        },
    }


def test_endpoint_upsert_and_api(monkeypatch) -> None:
    client = TestClient(app)
    project_id = create_project(client)

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

    discover_response = client.post(f"/api/projects/{project_id}/openapi/discover")
    assert discover_response.status_code == 200
    assert discover_response.json()["ok"] is True
    assert discover_response.json()["total_endpoints"] > 0

    endpoints_response = client.get(f"/api/projects/{project_id}/endpoints")
    assert endpoints_response.status_code == 200
    endpoints = endpoints_response.json()
    assert len(endpoints) == discover_response.json()["total_endpoints"]

    second_discover_response = client.post(f"/api/projects/{project_id}/openapi/discover")
    assert second_discover_response.status_code == 200
    assert second_discover_response.json()["created"] == 0
    assert second_discover_response.json()["updated"] == len(endpoints)

    endpoint_id = endpoints[0]["id"]
    detail_response = client.get(f"/api/projects/{project_id}/endpoints/{endpoint_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == endpoint_id

    client.delete(f"/api/projects/{project_id}")


def test_import_openapi_json_file_upserts_endpoints() -> None:
    client = TestClient(app)
    project_id = create_project(client)
    payload = sample_openapi_document()

    response = client.post(
        f"/api/projects/{project_id}/openapi/import-file",
        files={"file": ("openapi.json", json.dumps(payload), "application/json")},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is True
    assert result["created"] == 2
    assert result["updated"] == 0

    second_response = client.post(
        f"/api/projects/{project_id}/openapi/import-file",
        files={"file": ("openapi.json", json.dumps(payload), "application/json")},
    )
    assert second_response.status_code == 200
    assert second_response.json()["created"] == 0
    assert second_response.json()["updated"] == 2

    endpoints = client.get(f"/api/projects/{project_id}/endpoints").json()
    assert {endpoint["source"] for endpoint in endpoints} == {"openapi_file"}

    client.delete(f"/api/projects/{project_id}")


def test_import_openapi_yaml_file() -> None:
    client = TestClient(app)
    project_id = create_project(client)

    yaml_document = """
openapi: 3.0.3
info:
  title: Demo API
  version: 1.0.0
paths:
  /api/health:
    get:
      summary: Health check
      responses:
        "200":
          description: OK
"""
    response = client.post(
        f"/api/projects/{project_id}/openapi/import-file",
        files={"file": ("openapi.yaml", yaml_document, "application/yaml")},
    )

    assert response.status_code == 200
    assert response.json()["created"] == 1
    endpoints = client.get(f"/api/projects/{project_id}/endpoints").json()
    assert endpoints[0]["path"] == "/api/health"
    assert endpoints[0]["source"] == "openapi_file"

    client.delete(f"/api/projects/{project_id}")


def test_import_openapi_file_validation_errors() -> None:
    client = TestClient(app)
    project_id = create_project(client)

    empty_response = client.post(
        f"/api/projects/{project_id}/openapi/import-file",
        files={"file": ("openapi.json", "", "application/json")},
    )
    assert empty_response.status_code == 400
    assert "empty" in empty_response.json()["detail"].lower()

    missing_paths_response = client.post(
        f"/api/projects/{project_id}/openapi/import-file",
        files={"file": ("openapi.json", '{"openapi":"3.0.3","info":{}}', "application/json")},
    )
    assert missing_paths_response.status_code == 400
    assert "paths" in missing_paths_response.json()["detail"].lower()

    invalid_json_response = client.post(
        f"/api/projects/{project_id}/openapi/import-file",
        files={"file": ("openapi.json", "{", "application/json")},
    )
    assert invalid_json_response.status_code == 400
    assert "json" in invalid_json_response.json()["detail"].lower()

    client.delete(f"/api/projects/{project_id}")


def test_manual_endpoint_crud() -> None:
    client = TestClient(app)
    project_id = create_project(client)

    payload = {
        "method": "POST",
        "path": "/api/manual-users",
        "summary": "Create manual user",
        "description": "Created from API Map.",
        "tags": ["manual"],
        "request_body_schema": {"type": "object", "properties": {"name": {"type": "string"}}},
        "response_schema": {"type": "object", "properties": {"id": {"type": "integer"}}},
        "auth_required": True,
    }

    create_response = client.post(f"/api/projects/{project_id}/endpoints", json=payload)
    assert create_response.status_code == 201
    endpoint = create_response.json()
    assert endpoint["source"] == "manual"
    assert endpoint["path"] == "/api/manual-users"

    duplicate_response = client.post(f"/api/projects/{project_id}/endpoints", json=payload)
    assert duplicate_response.status_code == 409

    update_payload = {**payload, "method": "GET", "path": "/api/manual-users/{id}", "summary": "Get manual user"}
    update_response = client.put(
        f"/api/projects/{project_id}/endpoints/{endpoint['id']}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["method"] == "GET"
    assert update_response.json()["path_params"] == []

    endpoints = client.get(f"/api/projects/{project_id}/endpoints").json()
    assert any(item["id"] == endpoint["id"] for item in endpoints)

    delete_response = client.delete(f"/api/projects/{project_id}/endpoints/{endpoint['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True
    assert client.get(f"/api/projects/{project_id}/endpoints/{endpoint['id']}").status_code == 404

    client.delete(f"/api/projects/{project_id}")


def test_endpoint_project_not_found() -> None:
    client = TestClient(app)

    response = client.get("/api/projects/999999/endpoints")

    assert response.status_code == 404
