from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("api_endpoints.id"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(12), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    request_headers_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    request_query_params_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    request_path_params_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    request_body_json: Mapped[str] = mapped_column(Text, nullable=False, default="null")
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_headers_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    response_body_json: Mapped[str] = mapped_column(Text, nullable=False, default="null")
    db_changes_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="failed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
