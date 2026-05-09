from typing import Any

from app.adapters.database.base import DatabaseConnectionAdapter
from app.schemas.db_schema import DatabaseSchema


class MysqlAdapter(DatabaseConnectionAdapter):
    def test_connection(self, config: dict[str, Any]) -> tuple[bool, str]:
        try:
            import pymysql
        except ImportError:
            return False, "MySQL driver is not installed."

        required = ("host", "port", "database", "username")
        missing = [key for key in required if not config.get(key)]
        if missing:
            return False, f"MySQL config missing: {', '.join(missing)}."

        try:
            connection = pymysql.connect(
                host=str(config["host"]),
                port=int(config["port"]),
                database=str(config["database"]),
                user=str(config["username"]),
                password=str(config.get("password") or ""),
                connect_timeout=5,
            )
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except Exception as exc:
            return False, f"MySQL connection failed: {exc.__class__.__name__}."

        return True, "Database connection succeeded."

    def inspect_schema(self, config: dict[str, Any], project_id: int) -> DatabaseSchema:
        raise NotImplementedError("MySQL introspection is not implemented in Phase 3.")
