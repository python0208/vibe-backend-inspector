from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatabaseColumn(BaseModel):
    name: str
    type: str | None = None
    nullable: bool
    default: Any | None = None
    primary_key: bool = False


class DatabaseIndex(BaseModel):
    name: str
    columns: list[str] = Field(default_factory=list)
    unique: bool = False


class DatabaseForeignKey(BaseModel):
    column: str
    referenced_table: str
    referenced_column: str


class DatabaseTable(BaseModel):
    name: str
    row_count: int
    columns: list[DatabaseColumn] = Field(default_factory=list)
    indexes: list[DatabaseIndex] = Field(default_factory=list)
    foreign_keys: list[DatabaseForeignKey] = Field(default_factory=list)
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    project_id: int
    database_type: str
    database_name: str
    inspected_at: datetime
    tables: list[DatabaseTable] = Field(default_factory=list)


class DatabaseInspectResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ok: bool
    message: str
    database_schema: DatabaseSchema | None = Field(default=None, alias="schema")


class DatabaseProjectConnectionTestResponse(BaseModel):
    ok: bool
    message: str
    database_type: str
