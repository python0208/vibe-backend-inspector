from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


DatabaseType = Literal["none", "sqlite", "mysql", "postgres"]
AuthType = Literal["none", "bearer", "basic", "custom_headers"]


class AuthConfig(BaseModel):
    type: AuthType = "none"
    token: str | None = None
    username: str | None = None
    password: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    project_path: str = Field(min_length=1)
    service_base_url: str = Field(min_length=1)
    openapi_url: str | None = None
    database_type: DatabaseType = "none"
    database_config: dict[str, Any] = Field(default_factory=dict)
    auth_config: AuthConfig = Field(default_factory=AuthConfig)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    project_path: str | None = Field(default=None, min_length=1)
    service_base_url: str | None = Field(default=None, min_length=1)
    openapi_url: str | None = None
    database_type: DatabaseType | None = None
    database_config: dict[str, Any] | None = None
    auth_config: AuthConfig | None = None


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListItem(BaseModel):
    id: int
    name: str
    project_path: str
    service_base_url: str
    openapi_url: str | None = None
    database_type: DatabaseType
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
