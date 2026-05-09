from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import ensure_data_dir, get_settings


class Base(DeclarativeBase):
    pass


ensure_data_dir()
engine = create_engine(
    get_settings().database_url,
    connect_args={"check_same_thread": False}
    if get_settings().database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_compatible_columns()


def _ensure_compatible_columns() -> None:
    inspector = inspect(engine)
    if "test_runs" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("test_runs")}
    if "db_changes_json" in columns:
        return
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE test_runs ADD COLUMN db_changes_json TEXT NOT NULL DEFAULT '{}'"))
