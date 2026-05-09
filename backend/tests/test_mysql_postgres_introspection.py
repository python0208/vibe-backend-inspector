from datetime import UTC, datetime

from app.adapters.database.mysql_adapter import MysqlAdapter
from app.adapters.database.postgres_adapter import PostgresAdapter
from app.models.project import Project
from app.schemas.db_schema import DatabaseSchema, DatabaseTable
from app.services.snapshot_service import SnapshotService


class FakeCursor:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.current: object = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def execute(self, query, params=None) -> None:
        self.current = self.responses.pop(0)

    def fetchall(self):
        return self.current

    def fetchone(self):
        if isinstance(self.current, list):
            return self.current[0]
        return self.current


class FakeConnection:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def cursor(self):
        return FakeCursor(self.responses)


def test_mysql_inspect_schema_with_mock_connection(monkeypatch) -> None:
    responses: list[object] = [
        [{"table_name": "orders"}, {"table_name": "users"}],
        [{"table_name": "users", "column_name": "id"}],
        [
            {
                "table_name": "orders",
                "column_name": "id",
                "column_type": "int",
                "is_nullable": "NO",
                "column_default": None,
            },
            {
                "table_name": "orders",
                "column_name": "user_id",
                "column_type": "int",
                "is_nullable": "NO",
                "column_default": None,
            },
            {
                "table_name": "users",
                "column_name": "id",
                "column_type": "int",
                "is_nullable": "NO",
                "column_default": None,
            },
            {
                "table_name": "users",
                "column_name": "password_token",
                "column_type": "varchar(255)",
                "is_nullable": "YES",
                "column_default": None,
            },
        ],
        [
            {
                "table_name": "users",
                "index_name": "PRIMARY",
                "column_name": "id",
                "non_unique": 0,
            },
            {
                "table_name": "orders",
                "index_name": "idx_orders_user_id",
                "column_name": "user_id",
                "non_unique": 1,
            },
        ],
        [
            {
                "table_name": "orders",
                "column_name": "user_id",
                "referenced_table_name": "users",
                "referenced_column_name": "id",
            }
        ],
        {"count": 1},
        [{"id": 10, "user_id": 1}],
        {"count": 1},
        [{"id": 1, "password_token": "super-secret"}],
    ]

    def fake_connect(**kwargs):
        return FakeConnection(responses)

    monkeypatch.setattr("pymysql.connect", fake_connect)

    schema = MysqlAdapter().inspect_schema(
        {
            "host": "localhost",
            "port": 3306,
            "database": "demo",
            "username": "root",
            "password": "secret",
        },
        project_id=42,
    )

    assert schema.project_id == 42
    assert schema.database_type == "mysql"
    assert schema.database_name == "demo"
    assert [table.name for table in schema.tables] == ["orders", "users"]
    users = next(table for table in schema.tables if table.name == "users")
    assert users.row_count == 1
    assert users.sample_rows[0]["password_token"] == "********"
    assert any(column.name == "id" and column.primary_key for column in users.columns)
    orders = next(table for table in schema.tables if table.name == "orders")
    assert orders.foreign_keys[0].referenced_table == "users"
    assert any(index.name == "idx_orders_user_id" for index in orders.indexes)


def test_postgres_inspect_schema_with_mock_connection(monkeypatch) -> None:
    responses: list[object] = [
        [{"table_name": "orders"}, {"table_name": "users"}],
        [{"table_name": "users", "column_name": "id"}],
        [
            {
                "table_name": "orders",
                "column_name": "id",
                "data_type": "integer",
                "udt_name": "int4",
                "is_nullable": "NO",
                "column_default": None,
            },
            {
                "table_name": "orders",
                "column_name": "user_id",
                "data_type": "integer",
                "udt_name": "int4",
                "is_nullable": "NO",
                "column_default": None,
            },
            {
                "table_name": "users",
                "column_name": "id",
                "data_type": "integer",
                "udt_name": "int4",
                "is_nullable": "NO",
                "column_default": None,
            },
            {
                "table_name": "users",
                "column_name": "api_secret",
                "data_type": "text",
                "udt_name": "text",
                "is_nullable": "YES",
                "column_default": None,
            },
        ],
        [
            {
                "table_name": "users",
                "index_name": "users_pkey",
                "is_unique": True,
                "columns": ["id"],
            },
            {
                "table_name": "orders",
                "index_name": "idx_orders_user_id",
                "is_unique": False,
                "columns": ["user_id"],
            },
        ],
        [
            {
                "table_name": "orders",
                "column_name": "user_id",
                "referenced_table_name": "users",
                "referenced_column_name": "id",
            }
        ],
        {"count": 1},
        [{"id": 10, "user_id": 1}],
        {"count": 1},
        [{"id": 1, "api_secret": "super-secret"}],
    ]

    def fake_connect(**kwargs):
        return FakeConnection(responses)

    monkeypatch.setattr("psycopg.connect", fake_connect)

    schema = PostgresAdapter().inspect_schema(
        {
            "host": "localhost",
            "port": 5432,
            "database": "demo",
            "username": "postgres",
            "password": "secret",
        },
        project_id=43,
    )

    assert schema.project_id == 43
    assert schema.database_type == "postgres"
    assert schema.database_name == "demo"
    assert [table.name for table in schema.tables] == ["orders", "users"]
    users = next(table for table in schema.tables if table.name == "users")
    assert users.sample_rows[0]["api_secret"] == "********"
    assert any(column.name == "id" and column.primary_key for column in users.columns)
    orders = next(table for table in schema.tables if table.name == "orders")
    assert orders.foreign_keys[0].referenced_column == "id"
    assert any(index.name == "idx_orders_user_id" for index in orders.indexes)


def test_snapshot_service_uses_database_service_for_non_sqlite(monkeypatch) -> None:
    project = Project(
        id=7,
        name="Postgres Demo",
        project_path="D:/demo",
        service_base_url="http://example.test",
        database_type="postgres",
        database_config_json="{}",
    )
    schema = DatabaseSchema(
        project_id=7,
        database_type="postgres",
        database_name="demo",
        inspected_at=datetime.now(UTC),
        tables=[DatabaseTable(name="users", row_count=2, columns=[], indexes=[], foreign_keys=[])],
    )

    def fake_inspect_project_database(self, inspected_project):
        class Response:
            ok = True
            message = "ok"
            database_schema = schema

        return Response()

    monkeypatch.setattr(
        "app.services.snapshot_service.DatabaseService.inspect_project_database",
        fake_inspect_project_database,
    )

    snapshot = SnapshotService().capture_project_snapshot(project)

    assert snapshot.status == "captured"
    assert snapshot.database_type == "postgres"
    assert snapshot.tables["users"].row_count == 2
