import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.adapters.database.base import DatabaseConnectionAdapter
from app.schemas.db_schema import (
    DatabaseColumn,
    DatabaseForeignKey,
    DatabaseIndex,
    DatabaseSchema,
    DatabaseTable,
)


class SqliteAdapter(DatabaseConnectionAdapter):
    def test_connection(self, config: dict[str, Any]) -> tuple[bool, str]:
        database_path = config.get("database_path")
        if not database_path:
            return False, "SQLite database_path is required."

        path = Path(str(database_path))
        if not path.exists():
            return False, "SQLite database file does not exist."

        try:
            with sqlite3.connect(path) as connection:
                connection.execute("SELECT 1")
        except sqlite3.Error as exc:
            return False, f"SQLite connection failed: {exc.__class__.__name__}."

        return True, "Database connection succeeded."

    def inspect_schema(self, config: dict[str, Any], project_id: int) -> DatabaseSchema:
        database_path = config.get("database_path")
        if not database_path:
            raise ValueError("SQLite database_path is required.")

        path = Path(str(database_path))
        if not path.exists():
            raise ValueError("SQLite database file does not exist.")

        try:
            with sqlite3.connect(path) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("PRAGMA foreign_keys = ON")
                tables = [
                    self._inspect_table(connection, row["name"])
                    for row in connection.execute(
                        """
                        SELECT name
                        FROM sqlite_master
                        WHERE type = 'table'
                          AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                        """
                    ).fetchall()
                ]
        except sqlite3.Error as exc:
            raise ValueError(f"SQLite introspection failed: {exc.__class__.__name__}.") from exc

        return DatabaseSchema(
            project_id=project_id,
            database_type="sqlite",
            database_name=path.name,
            inspected_at=datetime.now(UTC),
            tables=tables,
        )

    def _inspect_table(self, connection: sqlite3.Connection, table_name: str) -> DatabaseTable:
        columns = self._inspect_columns(connection, table_name)
        indexes = self._inspect_indexes(connection, table_name)
        foreign_keys = self._inspect_foreign_keys(connection, table_name)
        row_count = self._row_count(connection, table_name)
        sample_rows = self._sample_rows(connection, table_name)

        return DatabaseTable(
            name=table_name,
            row_count=row_count,
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            sample_rows=sample_rows,
        )

    def _inspect_columns(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[DatabaseColumn]:
        rows = connection.execute(f"PRAGMA table_info({self._quote_identifier(table_name)})").fetchall()
        return [
            DatabaseColumn(
                name=row["name"],
                type=row["type"],
                nullable=not bool(row["notnull"]),
                default=row["dflt_value"],
                primary_key=bool(row["pk"]),
            )
            for row in rows
        ]

    def _inspect_indexes(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[DatabaseIndex]:
        indexes: list[DatabaseIndex] = []
        rows = connection.execute(f"PRAGMA index_list({self._quote_identifier(table_name)})").fetchall()
        for row in rows:
            index_name = row["name"]
            column_rows = connection.execute(
                f"PRAGMA index_info({self._quote_identifier(index_name)})"
            ).fetchall()
            indexes.append(
                DatabaseIndex(
                    name=index_name,
                    columns=[column["name"] for column in column_rows],
                    unique=bool(row["unique"]),
                )
            )
        return indexes

    def _inspect_foreign_keys(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[DatabaseForeignKey]:
        rows = connection.execute(f"PRAGMA foreign_key_list({self._quote_identifier(table_name)})").fetchall()
        return [
            DatabaseForeignKey(
                column=row["from"],
                referenced_table=row["table"],
                referenced_column=row["to"],
            )
            for row in rows
        ]

    def _row_count(self, connection: sqlite3.Connection, table_name: str) -> int:
        row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {self._quote_identifier(table_name)}"
        ).fetchone()
        return int(row["count"])

    def _sample_rows(self, connection: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
        rows = connection.execute(
            f"SELECT * FROM {self._quote_identifier(table_name)} LIMIT 20"
        ).fetchall()
        return [self._serialize_row(row) for row in rows]

    @staticmethod
    def _serialize_row(row: sqlite3.Row) -> dict[str, Any]:
        serialized: dict[str, Any] = {}
        for key in row.keys():
            value = row[key]
            if isinstance(value, bytes):
                serialized[key] = "<binary>"
            else:
                serialized[key] = value
        return serialized

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'
