from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApiEndpoint(Base):
    __tablename__ = "api_endpoints"
    __table_args__ = (
        UniqueConstraint("project_id", "method", "path", name="uq_endpoint_project_method_path"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(12), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    query_params_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    path_params_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    request_body_schema_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    response_schema_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    auth_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="openapi")
    test_status: Mapped[str] = mapped_column(String(40), nullable=False, default="untested")
    last_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
