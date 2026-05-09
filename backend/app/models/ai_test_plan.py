from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AITestPlanRecord(Base):
    __tablename__ = "ai_test_plans"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    llm_config_id: Mapped[int] = mapped_column(ForeignKey("llm_configs.id"), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(40), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AITestStepRecord(Base):
    __tablename__ = "ai_test_steps"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, index=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("ai_test_plans.id"), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("api_endpoints.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    step_json: Mapped[str] = mapped_column(Text, nullable=False)
    result_test_run_id: Mapped[int | None] = mapped_column(ForeignKey("test_runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
