from app.schemas.api_endpoint import EndpointUpsertPayload
from app.services.openapi_service import OpenApiService


def sample_openapi_document() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Demo API", "version": "1.0.0"},
        "security": [{"BearerAuth": []}],
        "paths": {
            "/api/users": {
                "get": {
                    "summary": "List users",
                    "operationId": "listUsers",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "array", "items": {"type": "object"}}
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Create user",
                    "operationId": "createUser",
                    "tags": ["users"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"name": {"type": "string"}},
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}},
                },
            },
            "/api/users/{id}": {
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "get": {
                    "summary": "Get user",
                    "operationId": "getUser",
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }


def test_parse_openapi_paths() -> None:
    endpoints = OpenApiService().parse_endpoints(sample_openapi_document())

    assert len(endpoints) == 3
    list_users = next(endpoint for endpoint in endpoints if endpoint.method == "GET" and endpoint.path == "/api/users")
    assert list_users.summary == "List users"
    assert list_users.operation_id == "listUsers"
    assert list_users.tags == ["users"]
    assert list_users.query_params[0]["name"] == "page"
    assert list_users.auth_required is True

    get_user = next(endpoint for endpoint in endpoints if endpoint.path == "/api/users/{id}")
    assert get_user.path_params[0]["name"] == "id"

    create_user = next(endpoint for endpoint in endpoints if endpoint.method == "POST")
    assert create_user.request_body_schema["properties"]["name"]["type"] == "string"


def test_parse_swagger_body_parameter() -> None:
    document = {
        "swagger": "2.0",
        "info": {"title": "Legacy", "version": "1.0"},
        "paths": {
            "/api/items": {
                "post": {
                    "parameters": [
                        {"name": "body", "in": "body", "schema": {"type": "object"}}
                    ],
                    "responses": {"200": {"schema": {"type": "object"}}},
                }
            }
        },
    }

    endpoints = OpenApiService().parse_endpoints(document, source="swagger")

    assert len(endpoints) == 1
    assert endpoints[0].request_body_schema == {"type": "object"}
    assert endpoints[0].response_schema == {"type": "object"}
