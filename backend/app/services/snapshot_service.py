import json
from dataclasses import dataclass, field
from typing import Any

from app.models.project import Project
from app.schemas.db_schema import DatabaseSchema, DatabaseTable
from app.schemas.test_run import DbChanges
from app.services.database_service import DatabaseService


SENSITIVE_SAMPLE_KEYS = ("password", "token", "secret", "credential")


@dataclass
class TableSnapshot:
    row_count: int
    columns: list[dict[str, Any]] = field(default_factory=list)
    sample_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DatabaseSnapshot:
    status: str
    database_type: str
    database_name: str | None = None
    captured_at: str | None = None
    table_count: int = 0
    tables: dict[str, TableSnapshot] = field(default_factory=dict)
    warning_message: str | None = None


class SnapshotService:
    def capture_project_snapshot(self, project: Project) -> DatabaseSnapshot:
        if project.database_type == "none":
            return DatabaseSnapshot(
                status="skipped",
                database_type=project.database_type,
                warning_message="No database configured.",
            )
        if project.database_type != "sqlite":
            return DatabaseSnapshot(
                status="skipped",
                database_type=project.database_type,
                warning_message="Database snapshot comparison currently supports SQLite only.",
            )

        response = DatabaseService().inspect_project_database(project)
        if not response.ok or not response.database_schema:
            return DatabaseSnapshot(
                status="error",
                database_type=project.database_type,
                warning_message=response.message,
            )

        return self._from_database_schema(response.database_schema)

    def compare_snapshots(
        self,
        before: DatabaseSnapshot,
        after: DatabaseSnapshot,
    ) -> DbChanges:
        if before.status == "skipped":
            return DbChanges(status="skipped", warning_message=before.warning_message)
        if after.status == "skipped":
            return DbChanges(status="skipped", warning_message=after.warning_message)
        if before.status == "error":
            return DbChanges(status="error", warning_message=before.warning_message)
        if after.status == "error":
            return DbChanges(status="error", warning_message=after.warning_message)

        before_names = set(before.tables)
        after_names = set(after.tables)
        tables_added = sorted(after_names - before_names)
        tables_removed = sorted(before_names - after_names)
        row_count_diff: dict[str, dict[str, int]] = {}
        schema_diff: dict[str, dict[str, list[str]]] = {}
        sample_diff: dict[str, dict[str, list[dict[str, Any]]]] = {}
        modified_tables: set[str] = set(tables_added + tables_removed)

        for table_name in sorted(before_names & after_names):
            before_table = before.tables[table_name]
            after_table = after.tables[table_name]
            if before_table.row_count != after_table.row_count:
                row_count_diff[table_name] = {
                    "before": before_table.row_count,
                    "after": after_table.row_count,
                    "diff": after_table.row_count - before_table.row_count,
                }
                modified_tables.add(table_name)

            table_schema_diff = self._diff_columns(before_table.columns, after_table.columns)
            if any(table_schema_diff.values()):
                schema_diff[table_name] = table_schema_diff
                modified_tables.add(table_name)

            if self._stable_json(before_table.sample_rows) != self._stable_json(after_table.sample_rows):
                sample_diff[table_name] = {
                    "before": self._mask_sample_rows(before_table.sample_rows),
                    "after": self._mask_sample_rows(after_table.sample_rows),
                }
                modified_tables.add(table_name)

        changed = bool(tables_added or tables_removed or row_count_diff or schema_diff or sample_diff)
        return DbChanges(
            status="captured",
            changed=changed,
            tables_added=tables_added,
            tables_removed=tables_removed,
            tables_modified=sorted(modified_tables),
            row_count_diff=row_count_diff,
            schema_diff=schema_diff,
            sample_diff=sample_diff,
            warning_message=None,
        )

    def _from_database_schema(self, schema: DatabaseSchema) -> DatabaseSnapshot:
        tables = {
            table.name: TableSnapshot(
                row_count=table.row_count,
                columns=self._normalize_columns(table),
                sample_rows=table.sample_rows,
            )
            for table in schema.tables
        }
        return DatabaseSnapshot(
            status="captured",
            database_type=schema.database_type,
            database_name=schema.database_name,
            captured_at=schema.inspected_at.isoformat(),
            table_count=len(schema.tables),
            tables=tables,
        )

    @staticmethod
    def _normalize_columns(table: DatabaseTable) -> list[dict[str, Any]]:
        return sorted(
            [
                {
                    "name": column.name,
                    "type": column.type,
                    "nullable": column.nullable,
                    "default": column.default,
                    "primary_key": column.primary_key,
                }
                for column in table.columns
            ],
            key=lambda column: column["name"],
        )

    @staticmethod
    def _diff_columns(
        before_columns: list[dict[str, Any]],
        after_columns: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        before_by_name = {str(column["name"]): column for column in before_columns}
        after_by_name = {str(column["name"]): column for column in after_columns}
        before_names = set(before_by_name)
        after_names = set(after_by_name)
        changed = sorted(
            name
            for name in before_names & after_names
            if before_by_name[name] != after_by_name[name]
        )
        return {
            "columns_added": sorted(after_names - before_names),
            "columns_removed": sorted(before_names - after_names),
            "columns_changed": changed,
        }

    @classmethod
    def _mask_sample_rows(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                key: "********" if cls._is_sensitive_key(key) else value
                for key, value in row.items()
            }
            for row in rows
        ]

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        normalized = key.lower()
        return any(marker in normalized for marker in SENSITIVE_SAMPLE_KEYS)

    @staticmethod
    def _stable_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
