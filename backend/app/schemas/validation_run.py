from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ValidationRunStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
ValidationRunItemStatus = Literal["pending", "running", "passed", "failed", "skipped"]
ValidationMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
ValidationFailureCategory = Literal[
    "validation_error",
    "auth_required",
    "permission_denied",
    "not_found",
    "server_error",
    "skipped_safety",
    "needs_user_input",
    "network_error",
    "unknown",
]


class ValidationRunCreate(BaseModel):
    name: str | None = None
    endpoint_ids: list[int] = Field(default_factory=list)
    methods: list[ValidationMethod] = Field(default_factory=list)
    skip_destructive: bool = True
    include_get: bool = True
    include_post: bool = True
    include_put_patch_delete: bool = False
    use_ai_generated_params: bool = False
    max_endpoints: int | None = Field(default=50, ge=1, le=100)


class ValidationRunItemRead(BaseModel):
    id: int
    validation_run_id: int
    project_id: int
    endpoint_id: int | None = None
    test_run_id: int | None = None
    method: str
    path: str
    status: str
    http_status: int | None = None
    response_time_ms: int | None = None
    error_message: str | None = None
    db_change_status: str | None = None
    request_headers: dict[str, Any] = Field(default_factory=dict)
    request_query_params: dict[str, Any] = Field(default_factory=dict)
    request_path_params: dict[str, Any] = Field(default_factory=dict)
    request_body: Any | None = None
    response_body_summary: Any | None = None
    db_changes: dict[str, Any] = Field(default_factory=dict)
    failure_category: str | None = None
    failure_reason: str | None = None
    suggestion: str | None = None
    order_index: int
    created_at: datetime
    updated_at: datetime


class ValidationRunRead(BaseModel):
    id: int
    project_id: int
    name: str
    status: str
    total_count: int
    passed_count: int
    failed_count: int
    skipped_count: int
    warning_count: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ValidationRunDetailRead(ValidationRunRead):
    items: list[ValidationRunItemRead] = Field(default_factory=list)


class ValidationRunCancelResponse(BaseModel):
    ok: bool
    message: str
    run: ValidationRunRead
