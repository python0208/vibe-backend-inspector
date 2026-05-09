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
        try:
            import psycopg
            from psycopg import sql
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise ValueError("PostgreSQL driver is not installed.") from exc

        self._validate_config(config)
        database_name = str(config["database"])
        schema_name = str(config.get("schema") or "public")

        try:
            with psycopg.connect(
                host=str(config["host"]),
                port=int(config["port"]),
                dbname=database_name,
                user=str(config["username"]),
                password=str(config.get("password") or ""),
                connect_timeout=5,
                row_factory=dict_row,
            ) as connection:
                with connection.cursor() as cursor:
                    table_names = self._table_names(cursor, schema_name)
                    primary_keys = self._primary_keys(cursor, schema_name)
                    columns_by_table = self._columns(cursor, schema_name, primary_keys)
                    indexes_by_table = self._indexes(cursor, schema_name)
                    foreign_keys_by_table = self._foreign_keys(cursor, schema_name)
                    tables = [
                        DatabaseTable(
                            name=table_name,
                            row_count=self._row_count(cursor, sql, schema_name, table_name),
                            columns=columns_by_table.get(table_name, []),
                            indexes=indexes_by_table.get(table_name, []),
                            foreign_keys=foreign_keys_by_table.get(table_name, []),
                            sample_rows=self._sample_rows(cursor, sql, schema_name, table_name),
                        )
                        for table_name in table_names
                    ]
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"PostgreSQL introspection failed: {exc.__class__.__name__}.") from exc

        return DatabaseSchema(
            project_id=project_id,
            database_type="postgres",
            database_name=database_name,
            inspected_at=datetime.now().astimezone(),
            tables=tables,
        )

    @staticmethod
    def _validate_config(config: dict[str, Any]) -> None:
        required = ("host", "port", "database", "username")
        missing = [key for key in required if not config.get(key)]
        if missing:
            raise ValueError(f"PostgreSQL config missing: {', '.join(missing)}.")

    @staticmethod
    def _table_names(cursor: Any, schema_name: str) -> list[str]:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            (schema_name,),
        )
        return [str(row["table_name"]) for row in cursor.fetchall()]

    @staticmethod
    def _primary_keys(cursor: Any, schema_name: str) -> dict[str, set[str]]:
        cursor.execute(
            """
            SELECT kcu.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_schema = kcu.constraint_schema
             AND tc.constraint_name = kcu.constraint_name
             AND tc.table_name = kcu.table_name
            WHERE tc.table_schema = %s
              AND tc.constraint_type = 'PRIMARY KEY'
            """,
            (schema_name,),
        )
        primary_keys: dict[str, set[str]] = {}
        for row in cursor.fetchall():
            primary_keys.setdefault(str(row["table_name"]), set()).add(str(row["column_name"]))
        return primary_keys

    @staticmethod
    def _columns(
        cursor: Any,
        schema_name: str,
        primary_keys: dict[str, set[str]],
    ) -> dict[str, list[DatabaseColumn]]:
        cursor.execute(
            """
            SELECT table_name, column_name, data_type, udt_name, is_nullable, column_default, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = %s
            ORDER BY table_name, ordinal_position
            """,
            (schema_name,),
        )
        columns: dict[str, list[DatabaseColumn]] = {}
        for row in cursor.fetchall():
            table_name = str(row["table_name"])
            column_name = str(row["column_name"])
            column_type = row.get("data_type") or row.get("udt_name")
            columns.setdefault(table_name, []).append(
                DatabaseColumn(
                    name=column_name,
                    type=column_type,
                    nullable=str(row.get("is_nullable")).upper() == "YES",
                    default=row.get("column_default"),
                    primary_key=column_name in primary_keys.get(table_name, set()),
                )
            )
        return columns

    @staticmethod
    def _indexes(cursor: Any, schema_name: str) -> dict[str, list[DatabaseIndex]]:
        cursor.execute(
            """
            SELECT
              table_class.relname AS table_name,
              index_class.relname AS index_name,
              pg_index.indisunique AS is_unique,
              array_agg(attribute.attname ORDER BY keys.ordinality) AS columns
            FROM pg_index
            JOIN pg_class table_class ON table_class.oid = pg_index.indrelid
            JOIN pg_namespace namespace ON namespace.oid = table_class.relnamespace
            JOIN pg_class index_class ON index_class.oid = pg_index.indexrelid
            JOIN LATERAL unnest(pg_index.indkey) WITH ORDINALITY AS keys(attnum, ordinality) ON TRUE
            JOIN pg_attribute attribute
              ON attribute.attrelid = table_class.oid
             AND attribute.attnum = keys.attnum
            WHERE namespace.nspname = %s
              AND table_class.relkind = 'r'
            GROUP BY table_class.relname, index_class.relname, pg_index.indisunique
            ORDER BY table_class.relname, index_class.relname
            """,
            (schema_name,),
        )
        indexes: dict[str, list[DatabaseIndex]] = {}
        for row in cursor.fetchall():
            table_name = str(row["table_name"])
            indexes.setdefault(table_name, []).append(
                DatabaseIndex(
                    name=str(row["index_name"]),
                    columns=[str(column) for column in row.get("columns", [])],
                    unique=bool(row["is_unique"]),
                )
            )
        return indexes

    @staticmethod
    def _foreign_keys(cursor: Any, schema_name: str) -> dict[str, list[DatabaseForeignKey]]:
        cursor.execute(
            """
            SELECT
              source_table.relname AS table_name,
              source_attribute.attname AS column_name,
              target_table.relname AS referenced_table_name,
              target_attribute.attname AS referenced_column_name
            FROM pg_constraint constraint_row
            JOIN pg_class source_table ON source_table.oid = constraint_row.conrelid
            JOIN pg_namespace namespace ON namespace.oid = source_table.relnamespace
            JOIN pg_class target_table ON target_table.oid = constraint_row.confrelid
            JOIN LATERAL unnest(constraint_row.conkey, constraint_row.confkey)
              AS key_map(source_attnum, target_attnum) ON TRUE
            JOIN pg_attribute source_attribute
              ON source_attribute.attrelid = source_table.oid
             AND source_attribute.attnum = key_map.source_attnum
            JOIN pg_attribute target_attribute
              ON target_attribute.attrelid = target_table.oid
             AND target_attribute.attnum = key_map.target_attnum
            WHERE constraint_row.contype = 'f'
              AND namespace.nspname = %s
            ORDER BY source_table.relname, constraint_row.conname
            """,
            (schema_name,),
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

    @staticmethod
    def _row_count(cursor: Any, sql_module: Any, schema_name: str, table_name: str) -> int:
        cursor.execute(
            sql_module.SQL("SELECT COUNT(*) AS count FROM {}.{}").format(
                sql_module.Identifier(schema_name),
                sql_module.Identifier(table_name),
            )
        )
        row = cursor.fetchone()
        return int(row["count"])

    def _sample_rows(
        self,
        cursor: Any,
        sql_module: Any,
        schema_name: str,
        table_name: str,
    ) -> list[dict[str, Any]]:
        cursor.execute(
            sql_module.SQL("SELECT * FROM {}.{} LIMIT 20").format(
                sql_module.Identifier(schema_name),
                sql_module.Identifier(table_name),
            )
        )
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
