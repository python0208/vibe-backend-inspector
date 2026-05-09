from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    endpoint_summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    test_summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    database_change_summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    ai_test_summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    issue_list_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    recommendation_list_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
