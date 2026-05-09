from fastapi.testclient import TestClient

from app.main import app


def test_project_crud() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/projects",
        json={
            "name": "Demo",
            "project_path": "D:/demo",
            "service_base_url": "http://localhost:8000",
            "openapi_url": "http://localhost:8000/openapi.json",
            "database_type": "sqlite",
            "database_config": {"database_path": "D:/demo/app.db", "password": "secret"},
            "auth_config": {"type": "bearer", "token": "secret-token"},
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Demo"
    assert created["database_config"]["password"] == "********"
    assert created["auth_config"]["token"] == "********"

    project_id = created["id"]
    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    assert any(project["id"] == project_id for project in list_response.json())

    update_response = client.put(
        f"/api/projects/{project_id}",
        json={
            "name": "Demo Updated",
            "project_path": "D:/demo",
            "service_base_url": "http://localhost:8000",
            "openapi_url": "http://localhost:8000/openapi.json",
            "database_type": "sqlite",
            "database_config": {"database_path": "D:/demo/app.db", "password": "********"},
            "auth_config": {"type": "bearer", "token": "********"},
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Demo Updated"
    assert update_response.json()["database_config"]["password"] == "********"
    assert update_response.json()["auth_config"]["token"] == "********"

    delete_response = client.delete(f"/api/projects/{project_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 404
