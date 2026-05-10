from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.test_run import TestRunRead


RiskLevel = Literal["low", "medium", "high"]
IssueSeverity = Literal["low", "medium", "high"]


class EndpointSummary(BaseModel):
    total: int = 0
    tested: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    untested: int = 0
    pass_rate: float = 0


class FailedEndpointReportItem(BaseModel):
    endpoint_id: int | None = None
    test_run_id: int | None = None
    method: str
    path: str
    summary: str | None = None
    http_status: int | None = None
    response_time_ms: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None


class TestSummary(BaseModel):
    total_runs: int = 0
    recent_runs: list[TestRunRead] = Field(default_factory=list)
    passed_runs: int = 0
    failed_runs: int = 0
    skipped_runs: int = 0
    average_response_time_ms: int | None = None
    validation_error_count: int = 0
    server_error_count: int = 0
    destructive_run_count: int = 0
    failed_endpoints: list[FailedEndpointReportItem] = Field(default_factory=list)


class RowCountAggregate(BaseModel):
    before: int | None = None
    after: int | None = None
    diff: int = 0


class DatabaseChangedTableItem(BaseModel):
    name: str
    row_count_diff: int = 0
    schema_changed: bool = False
    sample_changed: bool = False


class DatabaseChangeSummary(BaseModel):
    tests_with_db_changes: int = 0
    tests_with_db_errors: int = 0
    changed_tables: list[DatabaseChangedTableItem] = Field(default_factory=list)
    tables_added: list[str] = Field(default_factory=list)
    tables_removed: list[str] = Field(default_factory=list)
    tables_modified: list[str] = Field(default_factory=list)
    row_count_diff: dict[str, RowCountAggregate] = Field(default_factory=dict)
    schema_diff: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class AITestSummary(BaseModel):
    plan_count: int = 0
    latest_plan_id: str | None = None
    steps_total: int = 0
    steps_passed: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    steps_pending: int = 0
    destructive_steps: int = 0
    needs_input_steps: int = 0
    analysis_summary: str | None = None
    risk_levels: dict[str, int] = Field(default_factory=dict)


class ValidationRunSummary(BaseModel):
    latest_run_id: int | None = None
    name: str | None = None
    status: str | None = None
    total_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    warning_count: int = 0
    pass_rate: float = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ReportIssue(BaseModel):
    severity: IssueSeverity
    category: str
    title: str
    detail: str
    endpoint_id: int | None = None
    test_run_id: int | None = None
    method: str | None = None
    path: str | None = None


class ReportRecommendation(BaseModel):
    category: str
    title: str
    detail: str
    related_issue_category: str | None = None


class ReportSummaryRead(BaseModel):
    project_id: int
    project_name: str
    title: str
    generated_at: datetime
    overall_score: int
    risk_level: RiskLevel
    endpoint_summary: EndpointSummary
    test_summary: TestSummary
    database_change_summary: DatabaseChangeSummary
    ai_test_summary: AITestSummary
    validation_run_summary: ValidationRunSummary
    issue_list: list[ReportIssue] = Field(default_factory=list)
    recommendation_list: list[ReportRecommendation] = Field(default_factory=list)


class ReportRead(ReportSummaryRead):
    id: int
    markdown_content: str


class LatestReportResponse(BaseModel):
    ok: bool
    message: str
    report: ReportRead | None = None
