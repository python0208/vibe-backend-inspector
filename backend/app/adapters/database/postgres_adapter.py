from typing import Any

from app.adapters.database.base import DatabaseConnectionAdapter
from app.schemas.db_schema import DatabaseSchema


class PostgresAdapter(DatabaseConnectionAdapter):
    def test_connection(self, config: dict[str, Any]) -> tuple[bool, str]:
        try:
            import psycopg
        except ImportError:
            return False, "PostgreSQL driver is not installed."

        required = ("host", "port", "database", "username")
        missing = [key for key in required if not config.get(key)]
        if missing:
            return False, f"PostgreSQL config missing: {', '.join(missing)}."

        try:
            with psycopg.connect(
                host=str(config["host"]),
                port=int(config["port"]),
                dbname=str(config["database"]),
                user=str(config["username"]),
                password=str(config.get("password") or ""),
                connect_timeout=5,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except Exception as exc:
            return False, f"PostgreSQL connection failed: {exc.__class__.__name__}."

        return True, "Database connection succeeded."

    def inspect_schema(self, config: dict[str, Any], project_id: int) -> DatabaseSchema:
        raise NotImplementedError("PostgreSQL introspection is not implemented in Phase 3.")
