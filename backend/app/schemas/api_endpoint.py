from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
EndpointSource = Literal["openapi", "swagger"]
TestStatus = Literal["untested", "passed", "failed", "skipped"]


class EndpointBase(BaseModel):
    project_id: int
    method: str
    path: str
    summary: str | None = None
    description: str | None = None
    operation_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    query_params: list[dict[str, Any]] = Field(default_factory=list)
    path_params: list[dict[str, Any]] = Field(default_factory=list)
    request_body_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    auth_required: bool = False
    source: str = "openapi"
    test_status: str = "untested"
    last_status_code: int | None = None
    last_response_time_ms: int | None = None


class EndpointRead(EndpointBase):
    id: int
    created_at: datetime
    updated_at: datetime


class EndpointUpsertPayload(BaseModel):
    method: str
    path: str
    summary: str | None = None
    description: str | None = None
    operation_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    query_params: list[dict[str, Any]] = Field(default_factory=list)
    path_params: list[dict[str, Any]] = Field(default_factory=list)
    request_body_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    auth_required: bool = False
    source: str = "openapi"


class OpenApiDiscoveryResponse(BaseModel):
    ok: bool
    message: str
    project_id: int
    openapi_url: str | None = None
    total_endpoints: int = 0
    created: int = 0
    updated: int = 0
    attempted_urls: list[str] = Field(default_factory=list)
