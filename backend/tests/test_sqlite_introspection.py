import sqlite3

from app.adapters.database.sqlite_adapter import SqliteAdapter


def create_sample_database(database_path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                name TEXT DEFAULT 'anonymous'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                total REAL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute("CREATE INDEX idx_orders_user_id ON orders(user_id)")
        connection.execute("INSERT INTO users (email, name) VALUES ('alex@example.com', 'Alex')")
        connection.execute("INSERT INTO orders (user_id, total) VALUES (1, 42.5)")


def test_sqlite_inspect_schema(tmp_path) -> None:
    database_path = tmp_path / "sample.db"
    create_sample_database(database_path)

    schema = SqliteAdapter().inspect_schema({"database_path": str(database_path)}, project_id=7)

    assert schema.project_id == 7
    assert schema.database_type == "sqlite"
    assert schema.database_name == "sample.db"
    assert {table.name for table in schema.tables} == {"orders", "users"}

    users = next(table for table in schema.tables if table.name == "users")
    assert users.row_count == 1
    assert users.sample_rows[0]["email"] == "alex@example.com"
    assert any(column.name == "id" and column.primary_key for column in users.columns)
    assert any(column.name == "email" and column.nullable is False for column in users.columns)

    orders = next(table for table in schema.tables if table.name == "orders")
    assert orders.row_count == 1
    assert any(index.name == "idx_orders_user_id" and index.columns == ["user_id"] for index in orders.indexes)
    assert orders.foreign_keys[0].column == "user_id"
    assert orders.foreign_keys[0].referenced_table == "users"
    assert orders.foreign_keys[0].referenced_column == "id"
