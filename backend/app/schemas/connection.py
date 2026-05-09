from typing import Any

from pydantic import BaseModel, Field

from app.schemas.project import DatabaseType


class OpenApiTestRequest(BaseModel):
    url: str = Field(min_length=1)


class OpenApiTestResponse(BaseModel):
    ok: bool
    status_code: int | None = None
    message: str
    detected_format: str | None = None
    title: str | None = None


class DatabaseConnectionTestRequest(BaseModel):
    database_type: DatabaseType
    database_config: dict[str, Any] = Field(default_factory=dict)


class DatabaseConnectionTestResponse(BaseModel):
    ok: bool
    message: str
    database_type: DatabaseType
