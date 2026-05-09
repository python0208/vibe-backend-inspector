from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.adapters.database.base import DatabaseConnectionAdapter
from app.schemas.db_schema import (
    DatabaseColumn,
    DatabaseForeignKey,
    DatabaseIndex,
    DatabaseSchema,
    DatabaseTable,
)


SENSITIVE_SAMPLE_KEYS = ("password", "token", "secret", "credential")


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
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError as exc:
            raise ValueError("MySQL driver is not installed.") from exc

        self._validate_config(config)
        database_name = str(config["database"])

        try:
            connection = pymysql.connect(
                host=str(config["host"]),
                port=int(config["port"]),
                database=database_name,
                user=str(config["username"]),
                password=str(config.get("password") or ""),
                connect_timeout=5,
                cursorclass=DictCursor,
            )
            with connection:
                with connection.cursor() as cursor:
                    table_names = self._table_names(cursor, database_name)
                    primary_keys = self._primary_keys(cursor, database_name)
                    columns_by_table = self._columns(cursor, database_name, primary_keys)
                    indexes_by_table = self._indexes(cursor, database_name)
                    foreign_keys_by_table = self._foreign_keys(cursor, database_name)
                    tables = [
                        DatabaseTable(
                            name=table_name,
                            row_count=self._row_count(cursor, table_name),
                            columns=columns_by_table.get(table_name, []),
                            indexes=indexes_by_table.get(table_name, []),
                            foreign_keys=foreign_keys_by_table.get(table_name, []),
                            sample_rows=self._sample_rows(cursor, table_name),
                        )
                        for table_name in table_names
                    ]
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"MySQL introspection failed: {exc.__class__.__name__}.") from exc

        return DatabaseSchema(
            project_id=project_id,
            database_type="mysql",
            database_name=database_name,
            inspected_at=datetime.now().astimezone(),
            tables=tables,
        )

    @staticmethod
    def _validate_config(config: dict[str, Any]) -> None:
        required = ("host", "port", "database", "username")
        missing = [key for key in required if not config.get(key)]
        if missing:
            raise ValueError(f"MySQL config missing: {', '.join(missing)}.")

    @staticmethod
    def _table_names(cursor: Any, database_name: str) -> list[str]:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            (database_name,),
        )
        return [str(row["table_name"]) for row in cursor.fetchall()]

    @staticmethod
    def _primary_keys(cursor: Any, database_name: str) -> dict[str, set[str]]:
        cursor.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.key_column_usage
            WHERE table_schema = %s
              AND constraint_name = 'PRIMARY'
            """,
            (database_name,),
        )
        primary_keys: dict[str, set[str]] = {}
        for row in cursor.fetchall():
            primary_keys.setdefault(str(row["table_name"]), set()).add(str(row["column_name"]))
        return primary_keys

    @staticmethod
    def _columns(
        cursor: Any,
        database_name: str,
        primary_keys: dict[str, set[str]],
    ) -> dict[str, list[DatabaseColumn]]:
        cursor.execute(
            """
            SELECT table_name, column_name, column_type, is_nullable, column_default, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = %s
            ORDER BY table_name, ordinal_position
            """,
            (database_name,),
        )
        columns: dict[str, list[DatabaseColumn]] = {}
        for row in cursor.fetchall():
            table_name = str(row["table_name"])
            column_name = str(row["column_name"])
            columns.setdefault(table_name, []).append(
                DatabaseColumn(
                    name=column_name,
                    type=row.get("column_type"),
                    nullable=str(row.get("is_nullable")).upper() == "YES",
                    default=row.get("column_default"),
                    primary_key=column_name in primary_keys.get(table_name, set()),
                )
            )
        return columns

    @staticmethod
    def _indexes(cursor: Any, database_name: str) -> dict[str, list[DatabaseIndex]]:
        cursor.execute(
            """
            SELECT table_name, index_name, column_name, non_unique, seq_in_index
            FROM information_schema.statistics
            WHERE table_schema = %s
            ORDER BY table_name, index_name, seq_in_index
            """,
            (database_name,),
        )
        grouped: dict[str, dict[str, dict[str, Any]]] = {}
        for row in cursor.fetchall():
            table_name = str(row["table_name"])
            index_name = str(row["index_name"])
            grouped.setdefault(table_name, {}).setdefault(
                index_name,
                {"columns": [], "unique": int(row.get("non_unique") or 0) == 0},
            )
            grouped[table_name][index_name]["columns"].append(str(row["column_name"]))

        return {
            table_name: [
                DatabaseIndex(name=index_name, columns=data["columns"], unique=bool(data["unique"]))
                for index_name, data in indexes.items()
            ]
            for table_name, indexes in grouped.items()
        }

    @staticmethod
    def _foreign_keys(cursor: Any, database_name: str) -> dict[str, list[DatabaseForeignKey]]:
        cursor.execute(
            """
            SELECT table_name, column_name, referenced_table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_schema = %s
              AND referenced_table_name IS NOT NULL
              AND referenced_column_name IS NOT NULL
            ORDER BY table_name, constraint_name, ordinal_position
            """,
            (database_name,),
        )
        foreign_keys: dict[str, list[DatabaseForeignKey]] = {}
        for row in cursor.fetchall():
            table_name = str(row["table_name"])
            foreign_keys.setdefault(table_name, []).append(
                DatabaseForeignKey(
                    column=str(row["column_name"]),
                    referenced_table=str(row["referenced_table_name"]),
                    referenced_column=str(row["referenced_column_name"]),
                )
            )
        return foreign_keys

    def _row_count(self, cursor: Any, table_name: str) -> int:
        cursor.execute(f"SELECT COUNT(*) AS count FROM {self._quote_identifier(table_name)}")
        row = cursor.fetchone()
        return int(row["count"])

    def _sample_rows(self, cursor: Any, table_name: str) -> list[dict[str, Any]]:
        cursor.execute(f"SELECT * FROM {self._quote_identifier(table_name)} LIMIT 20")
        return [self._serialize_row(row) for row in cursor.fetchall()]

    @classmethod
    def _serialize_row(cls, row: dict[str, Any]) -> dict[str, Any]:
        serialized: dict[str, Any] = {}
        for key, value in row.items():
            if cls._is_sensitive_key(key):
                serialized[key] = "********" if value is not None else None
            elif isinstance(value, bytes):
                serialized[key] = "<binary>"
            elif isinstance(value, datetime | date):
                serialized[key] = value.isoformat()
            elif isinstance(value, Decimal):
                serialized[key] = str(value)
            else:
                serialized[key] = value
        return serialized

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        normalized = key.lower()
        return any(marker in normalized for marker in SENSITIVE_SAMPLE_KEYS)

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return "`" + identifier.replace("`", "``") + "`"
