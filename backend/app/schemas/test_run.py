from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


TestRunStatus = Literal["passed", "failed", "skipped"]
DbChangesStatus = Literal["captured", "skipped", "error"]


class RowCountDiff(BaseModel):
    before: int
    after: int
    diff: int


class TableSchemaDiff(BaseModel):
    columns_added: list[str] = Field(default_factory=list)
    columns_removed: list[str] = Field(default_factory=list)
    columns_changed: list[str] = Field(default_factory=list)


class TableSampleDiff(BaseModel):
    before: list[dict[str, Any]] = Field(default_factory=list)
    after: list[dict[str, Any]] = Field(default_factory=list)


class DbChanges(BaseModel):
    status: DbChangesStatus = "skipped"
    changed: bool = False
    tables_added: list[str] = Field(default_factory=list)
    tables_removed: list[str] = Field(default_factory=list)
    tables_modified: list[str] = Field(default_factory=list)
    row_count_diff: dict[str, RowCountDiff] = Field(default_factory=dict)
    schema_diff: dict[str, TableSchemaDiff] = Field(default_factory=dict)
    sample_diff: dict[str, TableSampleDiff] = Field(default_factory=dict)
    warning_message: str | None = None


class TestRequestPayload(BaseModel):
    path_params: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    bearer_token: str | None = None
    json_body: Any | None = None


class TestRunRead(BaseModel):
    id: int
    project_id: int
    endpoint_id: int
    method: str
    url: str
    request_headers: dict[str, Any] = Field(default_factory=dict)
    request_query_params: dict[str, Any] = Field(default_factory=dict)
    request_path_params: dict[str, Any] = Field(default_factory=dict)
    request_body: Any | None = None
    http_status: int | None = None
    response_time_ms: int | None = None
    response_headers: dict[str, Any] = Field(default_factory=dict)
    response_body: Any | None = None
    db_changes: DbChanges = Field(default_factory=DbChanges)
    status: TestRunStatus
    error_message: str | None = None
    created_at: datetime
