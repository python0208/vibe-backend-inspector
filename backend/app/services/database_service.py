import json
from typing import Any

from app.adapters.database.base import DatabaseConnectionAdapter
from app.adapters.database.mysql_adapter import MysqlAdapter
from app.adapters.database.postgres_adapter import PostgresAdapter
from app.adapters.database.sqlite_adapter import SqliteAdapter
from app.models.project import Project
from app.schemas.db_schema import DatabaseInspectResponse, DatabaseProjectConnectionTestResponse
from app.schemas.project import DatabaseType


class DatabaseService:
    def __init__(self) -> None:
        self.adapters: dict[str, DatabaseConnectionAdapter] = {
            "sqlite": SqliteAdapter(),
            "mysql": MysqlAdapter(),
            "postgres": PostgresAdapter(),
        }

    def test_connection(self, database_type: DatabaseType, config: dict[str, Any]) -> tuple[bool, str]:
        if database_type == "none":
            return True, "No database configured."

        adapter = self.adapters.get(database_type)
        if not adapter:
            return False, f"Unsupported database type: {database_type}."

        return adapter.test_connection(config)

    def test_project_connection(self, project: Project) -> DatabaseProjectConnectionTestResponse:
        database_type = project.database_type
        config = self._loads(project.database_config_json)
        ok, message = self.test_connection(database_type, config)
        return DatabaseProjectConnectionTestResponse(
            ok=ok,
            message=message,
            database_type=database_type,
        )

    def inspect_project_database(self, project: Project) -> DatabaseInspectResponse:
        database_type = project.database_type
        if database_type == "none":
            return DatabaseInspectResponse(
                ok=False,
                message="No database configured.",
                schema=None,
            )

        adapter = self.adapters.get(database_type)
        if not adapter:
            return DatabaseInspectResponse(
                ok=False,
                message=f"Unsupported database type: {database_type}.",
                schema=None,
            )

        try:
            schema = adapter.inspect_schema(self._loads(project.database_config_json), project.id)
        except NotImplementedError as exc:
            return DatabaseInspectResponse(ok=False, message=str(exc), schema=None)
        except ValueError as exc:
            return DatabaseInspectResponse(ok=False, message=str(exc), schema=None)

        return DatabaseInspectResponse(
            ok=True,
            message="Database schema inspected successfully.",
            schema=schema,
        )

    @staticmethod
    def _loads(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            loaded = json.loads(raw)
            return loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            return {}
