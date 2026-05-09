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


def test_endpoint_project_not_found() -> None:
    client = TestClient(app)

    response = client.get("/api/projects/999999/endpoints")

    assert response.status_code == 404
