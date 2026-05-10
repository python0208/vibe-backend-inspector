import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.ai_test_plan import AITestPlanRecord, AITestStepRecord
from app.models.api_endpoint import ApiEndpoint
from app.models.project import Project
from app.models.report import Report
from app.models.test_run import TestRun
from app.models.validation_run import ValidationRun
from app.schemas.ai_test import AITestPlan
from app.schemas.report import (
    AITestSummary,
    DatabaseChangedTableItem,
    DatabaseChangeSummary,
    EndpointSummary,
    FailedEndpointReportItem,
    LatestReportResponse,
    ReportIssue,
    ReportRead,
    ReportRecommendation,
    ReportSummaryRead,
    RowCountAggregate,
    TestSummary,
    ValidationRunSummary,
)
from app.services.endpoint_service import EndpointService
from app.services.project_service import ProjectService
from app.services.test_service import TestService


DESTRUCTIVE_METHODS = {"PUT", "PATCH", "DELETE"}
RECENT_RUN_LIMIT = 20
SUMMARY_RUN_LIMIT = 100


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build_summary(self, project_id: int) -> ReportSummaryRead:
        project = ProjectService(self.db).get_project(project_id)
        endpoints = EndpointService(self.db).list_endpoints(project_id)
        runs = self._list_runs(project_id, SUMMARY_RUN_LIMIT)
        recent_runs = runs[:RECENT_RUN_LIMIT]
        endpoint_by_id = {endpoint.id: endpoint for endpoint in endpoints}

        endpoint_summary = self._build_endpoint_summary(endpoints)
        test_summary = self._build_test_summary(runs, recent_runs, endpoint_by_id)
        database_summary = self._build_database_summary(runs)
        ai_summary = self._build_ai_summary(project_id)
        validation_summary = self._build_validation_summary(project_id)
        issue_list = self._build_issues(runs, endpoint_by_id, database_summary, ai_summary)
        recommendation_list = self._build_recommendations(
            endpoint_summary,
            test_summary,
            database_summary,
            ai_summary,
            issue_list,
        )
        overall_score = self._calculate_score(endpoint_summary, test_summary, database_summary, ai_summary)
        risk_level = self._calculate_risk(overall_score, test_summary, database_summary)

        return ReportSummaryRead(
            project_id=project.id,
            project_name=project.name,
            title=f"{project.name} Acceptance Report",
            generated_at=datetime.now(timezone.utc),
            overall_score=overall_score,
            risk_level=risk_level,
            endpoint_summary=endpoint_summary,
            test_summary=test_summary,
            database_change_summary=database_summary,
            ai_test_summary=ai_summary,
            validation_run_summary=validation_summary,
            issue_list=issue_list,
            recommendation_list=recommendation_list,
        )

    def generate_report(self, project_id: int) -> ReportRead:
        summary = self.build_summary(project_id)
        markdown = self._render_markdown(summary)
        report = Report(
            project_id=summary.project_id,
            title=summary.title,
            risk_level=summary.risk_level,
            overall_score=summary.overall_score,
            endpoint_summary_json=summary.endpoint_summary.model_dump_json(),
            test_summary_json=summary.test_summary.model_dump_json(),
            database_change_summary_json=summary.database_change_summary.model_dump_json(),
            ai_test_summary_json=summary.ai_test_summary.model_dump_json(),
            validation_run_summary_json=summary.validation_run_summary.model_dump_json(),
            issue_list_json=json.dumps([issue.model_dump(mode="json") for issue in summary.issue_list]),
            recommendation_list_json=json.dumps(
                [recommendation.model_dump(mode="json") for recommendation in summary.recommendation_list]
            ),
            markdown_content=markdown,
            generated_at=summary.generated_at,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return self.to_read_schema(report)

    def latest_report(self, project_id: int) -> LatestReportResponse:
        ProjectService(self.db).get_project(project_id)
        report = (
            self.db.query(Report)
            .filter(Report.project_id == project_id)
            .order_by(Report.generated_at.desc(), Report.id.desc())
            .first()
        )
        if not report:
            return LatestReportResponse(ok=True, message="No report generated yet.", report=None)
        return LatestReportResponse(ok=True, message="Latest report loaded.", report=self.to_read_schema(report))

    def get_report(self, project_id: int, report_id: int) -> Report:
        ProjectService(self.db).get_project(project_id)
        report = (
            self.db.query(Report)
            .filter(Report.project_id == project_id, Report.id == report_id)
            .first()
        )
        if not report:
            raise NotFoundError("Report not found.")
        return report

    def to_read_schema(self, report: Report) -> ReportRead:
        project = ProjectService(self.db).get_project(report.project_id)
        return ReportRead(
            id=report.id,
            project_id=report.project_id,
            project_name=project.name,
            title=report.title,
            generated_at=report.generated_at,
            overall_score=report.overall_score,
            risk_level=report.risk_level,
            endpoint_summary=EndpointSummary.model_validate(self._loads(report.endpoint_summary_json, {})),
            test_summary=TestSummary.model_validate(self._loads(report.test_summary_json, {})),
            database_change_summary=DatabaseChangeSummary.model_validate(
                self._loads(report.database_change_summary_json, {})
            ),
            ai_test_summary=AITestSummary.model_validate(self._loads(report.ai_test_summary_json, {})),
            validation_run_summary=ValidationRunSummary.model_validate(
                self._loads(getattr(report, "validation_run_summary_json", "{}"), {})
            ),
            issue_list=[
                ReportIssue.model_validate(item)
                for item in self._loads(report.issue_list_json, [])
                if isinstance(item, dict)
            ],
            recommendation_list=[
                ReportRecommendation.model_validate(item)
                for item in self._loads(report.recommendation_list_json, [])
                if isinstance(item, dict)
            ],
            markdown_content=report.markdown_content,
        )

    def _list_runs(self, project_id: int, limit: int) -> list[TestRun]:
        return (
            self.db.query(TestRun)
            .filter(TestRun.project_id == project_id)
            .order_by(TestRun.created_at.desc(), TestRun.id.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def _build_endpoint_summary(endpoints: list[ApiEndpoint]) -> EndpointSummary:
        counts = Counter(endpoint.test_status for endpoint in endpoints)
        tested = counts["passed"] + counts["failed"] + counts["skipped"]
        pass_rate = round((counts["passed"] / tested) * 100, 1) if tested else 0
        return EndpointSummary(
            total=len(endpoints),
            tested=tested,
            passed=counts["passed"],
            failed=counts["failed"],
            skipped=counts["skipped"],
            untested=len(endpoints) - tested,
            pass_rate=pass_rate,
        )

    def _build_test_summary(
        self,
        runs: list[TestRun],
        recent_runs: list[TestRun],
        endpoint_by_id: dict[int, ApiEndpoint],
    ) -> TestSummary:
        test_service = TestService(self.db)
        counts = Counter(run.status for run in runs)
        response_times = [run.response_time_ms for run in runs if run.response_time_ms is not None]
        failed_endpoints = [
            self._failed_endpoint_item(run, endpoint_by_id.get(run.endpoint_id))
            for run in runs
            if run.status == "failed"
        ][:20]
        return TestSummary(
            total_runs=len(runs),
            recent_runs=[test_service.to_read_schema(run) for run in recent_runs],
            passed_runs=counts["passed"],
            failed_runs=counts["failed"],
            skipped_runs=counts["skipped"],
            average_response_time_ms=round(sum(response_times) / len(response_times)) if response_times else None,
            validation_error_count=sum(1 for run in runs if run.http_status == 422),
            server_error_count=sum(1 for run in runs if run.http_status is not None and run.http_status >= 500),
            destructive_run_count=sum(1 for run in runs if run.method.upper() in DESTRUCTIVE_METHODS),
            failed_endpoints=failed_endpoints,
        )

    def _build_database_summary(self, runs: list[TestRun]) -> DatabaseChangeSummary:
        row_count_diff: dict[str, RowCountAggregate] = {}
        schema_diff: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: {"columns_added": set(), "columns_removed": set(), "columns_changed": set()}
        )
        changed_table_names: set[str] = set()
        sample_changed: set[str] = set()
        tables_added: set[str] = set()
        tables_removed: set[str] = set()
        tables_modified: set[str] = set()
        warnings: list[str] = []
        tests_with_db_changes = 0
        tests_with_db_errors = 0

        for run in runs:
            db_changes = self._loads(run.db_changes_json, {})
            if not isinstance(db_changes, dict):
                continue
            status = db_changes.get("status")
            if status == "error":
                tests_with_db_errors += 1
            if db_changes.get("changed"):
                tests_with_db_changes += 1

            for table in db_changes.get("tables_added", []) or []:
                tables_added.add(str(table))
                changed_table_names.add(str(table))
            for table in db_changes.get("tables_removed", []) or []:
                tables_removed.add(str(table))
                changed_table_names.add(str(table))
            for table in db_changes.get("tables_modified", []) or []:
                tables_modified.add(str(table))
                changed_table_names.add(str(table))

            for table, diff in (db_changes.get("row_count_diff") or {}).items():
                if not isinstance(diff, dict):
                    continue
                aggregate = row_count_diff.setdefault(str(table), RowCountAggregate())
                aggregate.diff += int(diff.get("diff") or 0)
                aggregate.before = diff.get("before") if aggregate.before is None else aggregate.before
                aggregate.after = diff.get("after")
                changed_table_names.add(str(table))

            for table, diff in (db_changes.get("schema_diff") or {}).items():
                if not isinstance(diff, dict):
                    continue
                table_key = str(table)
                changed_table_names.add(table_key)
                for key in ("columns_added", "columns_removed", "columns_changed"):
                    schema_diff[table_key][key].update(str(item) for item in diff.get(key, []) or [])

            for table in (db_changes.get("sample_diff") or {}).keys():
                sample_changed.add(str(table))
                changed_table_names.add(str(table))

            warning = db_changes.get("warning_message")
            if warning:
                warnings.append(str(warning))

        changed_tables = [
            DatabaseChangedTableItem(
                name=table,
                row_count_diff=row_count_diff.get(table, RowCountAggregate()).diff,
                schema_changed=table in schema_diff,
                sample_changed=table in sample_changed,
            )
            for table in sorted(changed_table_names)
        ]
        return DatabaseChangeSummary(
            tests_with_db_changes=tests_with_db_changes,
            tests_with_db_errors=tests_with_db_errors,
            changed_tables=changed_tables,
            tables_added=sorted(tables_added),
            tables_removed=sorted(tables_removed),
            tables_modified=sorted(tables_modified),
            row_count_diff=row_count_diff,
            schema_diff={
                table: {key: sorted(values) for key, values in diff.items()}
                for table, diff in schema_diff.items()
            },
            warnings=warnings[:20],
        )

    def _build_ai_summary(self, project_id: int) -> AITestSummary:
        plans = (
            self.db.query(AITestPlanRecord)
            .filter(AITestPlanRecord.project_id == project_id)
            .order_by(AITestPlanRecord.updated_at.desc(), AITestPlanRecord.created_at.desc())
            .limit(20)
            .all()
        )
        plan_ids = [plan.id for plan in plans]
        steps = []
        if plan_ids:
            steps = (
                self.db.query(AITestStepRecord)
                .filter(AITestStepRecord.project_id == project_id, AITestStepRecord.plan_id.in_(plan_ids))
                .all()
            )
        status_counts = Counter(step.status for step in steps)
        risk_counts = Counter(plan.risk_level for plan in plans)
        analysis_summary = None
        for plan in plans:
            loaded = self._loads(plan.analysis_json, {})
            if isinstance(loaded, dict) and loaded.get("analysis"):
                analysis_summary = str(loaded["analysis"])
                break
        return AITestSummary(
            plan_count=len(plans),
            latest_plan_id=plans[0].id if plans else None,
            steps_total=len(steps),
            steps_passed=status_counts["passed"],
            steps_failed=status_counts["failed"],
            steps_skipped=status_counts["skipped"],
            steps_pending=status_counts["pending"] + status_counts["running"],
            destructive_steps=self._count_destructive_steps(plans),
            needs_input_steps=self._count_needs_input_steps(plans),
            analysis_summary=analysis_summary,
            risk_levels=dict(risk_counts),
        )

    def _build_validation_summary(self, project_id: int) -> ValidationRunSummary:
        run = (
            self.db.query(ValidationRun)
            .filter(ValidationRun.project_id == project_id)
            .order_by(ValidationRun.created_at.desc(), ValidationRun.id.desc())
            .first()
        )
        if not run:
            return ValidationRunSummary()
        summary = self._loads(run.summary_json, {})
        pass_rate = summary.get("pass_rate") if isinstance(summary, dict) else None
        if pass_rate is None and run.total_count:
            pass_rate = round((run.passed_count / run.total_count) * 100, 1)
        return ValidationRunSummary(
            latest_run_id=run.id,
            name=run.name,
            status=run.status,
            total_count=run.total_count,
            passed_count=run.passed_count,
            failed_count=run.failed_count,
            skipped_count=run.skipped_count,
            warning_count=run.warning_count,
            pass_rate=float(pass_rate or 0),
            started_at=run.started_at,
            finished_at=run.finished_at,
        )

    def _build_issues(
        self,
        runs: list[TestRun],
        endpoint_by_id: dict[int, ApiEndpoint],
        database_summary: DatabaseChangeSummary,
        ai_summary: AITestSummary,
    ) -> list[ReportIssue]:
        issues: list[ReportIssue] = []
        for run in runs:
            endpoint = endpoint_by_id.get(run.endpoint_id)
            path = endpoint.path if endpoint else run.url
            if run.status == "failed":
                severity = "high" if run.http_status and run.http_status >= 500 else "medium"
                issues.append(
                    ReportIssue(
                        severity=severity,
                        category="endpoint",
                        title=f"{run.method} {path} failed",
                        detail=run.error_message or f"HTTP status: {run.http_status}",
                        endpoint_id=run.endpoint_id,
                        test_run_id=run.id,
                        method=run.method,
                        path=path,
                    )
                )
            if run.http_status == 422:
                issues.append(
                    ReportIssue(
                        severity="medium",
                        category="validation",
                        title="Validation error returned",
                        detail="The API returned HTTP 422. Review generated parameters and OpenAPI required fields.",
                        endpoint_id=run.endpoint_id,
                        test_run_id=run.id,
                        method=run.method,
                        path=path,
                    )
                )
            if run.http_status is not None and run.http_status >= 500:
                issues.append(
                    ReportIssue(
                        severity="high",
                        category="server_error",
                        title="Server error returned",
                        detail=f"The API returned HTTP {run.http_status}.",
                        endpoint_id=run.endpoint_id,
                        test_run_id=run.id,
                        method=run.method,
                        path=path,
                    )
                )
            db_changes = self._loads(run.db_changes_json, {})
            if isinstance(db_changes, dict) and db_changes.get("status") == "error":
                issues.append(
                    ReportIssue(
                        severity="medium",
                        category="database",
                        title="Database snapshot failed",
                        detail=str(db_changes.get("warning_message") or "Database snapshot diff could not be captured."),
                        endpoint_id=run.endpoint_id,
                        test_run_id=run.id,
                        method=run.method,
                        path=path,
                    )
                )
            if (
                run.method.upper() in DESTRUCTIVE_METHODS.union({"POST"})
                and isinstance(db_changes, dict)
                and db_changes.get("status") == "captured"
                and not db_changes.get("changed")
            ):
                issues.append(
                    ReportIssue(
                        severity="low",
                        category="database",
                        title="Write-like request produced no database changes",
                        detail="Confirm whether the operation is expected to be read-only or blocked by business logic.",
                        endpoint_id=run.endpoint_id,
                        test_run_id=run.id,
                        method=run.method,
                        path=path,
                    )
                )
        if ai_summary.steps_failed:
            issues.append(
                ReportIssue(
                    severity="medium",
                    category="ai_test",
                    title="AI smart test steps failed",
                    detail=f"{ai_summary.steps_failed} AI-assisted test step(s) failed.",
                )
            )
        if database_summary.tests_with_db_errors >= 3:
            issues.append(
                ReportIssue(
                    severity="high",
                    category="database",
                    title="Repeated database snapshot errors",
                    detail="Multiple test runs could not capture database snapshots.",
                )
            )
        return issues[:50]

    @staticmethod
    def _build_recommendations(
        endpoint_summary: EndpointSummary,
        test_summary: TestSummary,
        database_summary: DatabaseChangeSummary,
        ai_summary: AITestSummary,
        issues: list[ReportIssue],
    ) -> list[ReportRecommendation]:
        recommendations: list[ReportRecommendation] = []
        categories = {issue.category for issue in issues}
        if endpoint_summary.total and endpoint_summary.tested / endpoint_summary.total < 0.7:
            recommendations.append(
                ReportRecommendation(
                    category="coverage",
                    title="Increase endpoint test coverage",
                    detail="Run more endpoint tests before treating this report as final acceptance evidence.",
                )
            )
        if "validation" in categories or test_summary.validation_error_count:
            recommendations.append(
                ReportRecommendation(
                    category="request_params",
                    title="Review request parameters",
                    detail="422 responses usually mean required path, query, or body fields are missing or malformed.",
                    related_issue_category="validation",
                )
            )
        if "server_error" in categories or test_summary.server_error_count:
            recommendations.append(
                ReportRecommendation(
                    category="response_error",
                    title="Investigate server errors first",
                    detail="5xx responses indicate target backend failures and should be fixed before expanding test scope.",
                    related_issue_category="server_error",
                )
            )
        if database_summary.tests_with_db_errors:
            recommendations.append(
                ReportRecommendation(
                    category="database_change",
                    title="Fix database snapshot capture",
                    detail="Verify the configured test database path or connection before relying on db_changes evidence.",
                    related_issue_category="database",
                )
            )
        if any(issue.title == "Write-like request produced no database changes" for issue in issues):
            recommendations.append(
                ReportRecommendation(
                    category="database_change",
                    title="Confirm write operation effects",
                    detail="For POST, PUT, PATCH, and DELETE endpoints, check whether no database change is expected.",
                    related_issue_category="database",
                )
            )
        if ai_summary.plan_count and ai_summary.analysis_summary is None:
            recommendations.append(
                ReportRecommendation(
                    category="ai_test",
                    title="Run AI result analysis",
                    detail="Generate AI analysis for the latest smart test plan to include richer interpretation.",
                )
            )
        if not recommendations:
            recommendations.append(
                ReportRecommendation(
                    category="acceptance",
                    title="Keep validating new backend changes",
                    detail="No critical recommendation was generated from current test evidence.",
                )
            )
        return recommendations

    @staticmethod
    def _calculate_score(
        endpoint_summary: EndpointSummary,
        test_summary: TestSummary,
        database_summary: DatabaseChangeSummary,
        ai_summary: AITestSummary,
    ) -> int:
        if test_summary.total_runs == 0:
            return 0
        score = 100
        score -= min(test_summary.failed_runs * 8, 32)
        score -= min(test_summary.server_error_count * 10, 30)
        score -= min(test_summary.validation_error_count * 4, 16)
        score -= min(database_summary.tests_with_db_errors * 6, 18)
        score -= min(ai_summary.steps_failed * 5, 20)
        if endpoint_summary.total and endpoint_summary.tested / endpoint_summary.total < 0.5:
            score -= 10
        return max(score, 0)

    @staticmethod
    def _calculate_risk(
        overall_score: int,
        test_summary: TestSummary,
        database_summary: DatabaseChangeSummary,
    ) -> str:
        if (
            overall_score < 60
            or test_summary.server_error_count > 0
            or database_summary.tests_with_db_errors >= 3
        ):
            return "high"
        if (
            overall_score < 80
            or test_summary.failed_runs > 0
            or test_summary.validation_error_count > 0
            or database_summary.tests_with_db_errors > 0
        ):
            return "medium"
        return "low"

    @staticmethod
    def _failed_endpoint_item(run: TestRun, endpoint: ApiEndpoint | None) -> FailedEndpointReportItem:
        return FailedEndpointReportItem(
            endpoint_id=run.endpoint_id,
            test_run_id=run.id,
            method=run.method,
            path=endpoint.path if endpoint else run.url,
            summary=endpoint.summary if endpoint else None,
            http_status=run.http_status,
            response_time_ms=run.response_time_ms,
            error_message=run.error_message,
            created_at=run.created_at,
        )

    @staticmethod
    def _count_destructive_steps(plans: list[AITestPlanRecord]) -> int:
        count = 0
        for record in plans:
            try:
                plan = AITestPlan.model_validate(json.loads(record.plan_json))
            except (json.JSONDecodeError, ValueError):
                continue
            count += sum(1 for step in plan.steps if step.destructive or step.method.upper() in DESTRUCTIVE_METHODS)
        return count

    @staticmethod
    def _count_needs_input_steps(plans: list[AITestPlanRecord]) -> int:
        count = 0
        for record in plans:
            try:
                plan = AITestPlan.model_validate(json.loads(record.plan_json))
            except (json.JSONDecodeError, ValueError):
                continue
            count += sum(1 for step in plan.steps if step.needs_user_input)
        return count

    def _render_markdown(self, summary: ReportSummaryRead) -> str:
        endpoint = summary.endpoint_summary
        tests = summary.test_summary
        database = summary.database_change_summary
        ai = summary.ai_test_summary
        validation = summary.validation_run_summary
        lines = [
            f"# {summary.title}",
            "",
            f"- Project: {summary.project_name}",
            f"- Generated at: {summary.generated_at.isoformat()}",
            f"- Overall score: {summary.overall_score}/100",
            f"- Risk level: {summary.risk_level}",
            "",
            "## Endpoint Summary",
            "",
            f"- Total endpoints: {endpoint.total}",
            f"- Tested endpoints: {endpoint.tested}",
            f"- Passed / failed / skipped: {endpoint.passed} / {endpoint.failed} / {endpoint.skipped}",
            f"- Pass rate: {endpoint.pass_rate}%",
            "",
            "## Test Summary",
            "",
            f"- Total recent runs: {tests.total_runs}",
            f"- Passed / failed / skipped runs: {tests.passed_runs} / {tests.failed_runs} / {tests.skipped_runs}",
            f"- Average response time: {tests.average_response_time_ms or 0} ms",
            f"- 422 validation errors: {tests.validation_error_count}",
            f"- 5xx server errors: {tests.server_error_count}",
            "",
            "## Validation Run Summary",
            "",
            f"- Latest run: {validation.name or '-'}",
            f"- Status: {validation.status or '-'}",
            f"- Total endpoints: {validation.total_count}",
            f"- Passed / failed / skipped: {validation.passed_count} / {validation.failed_count} / {validation.skipped_count}",
            f"- Pass rate: {validation.pass_rate}%",
            "",
            "## Failed Endpoints",
            "",
            "| Method | Path | HTTP | Response Time | Error |",
            "| --- | --- | --- | --- | --- |",
        ]
        if tests.failed_endpoints:
            for item in tests.failed_endpoints:
                lines.append(
                    "| "
                    f"{item.method} | {self._md(item.path)} | {item.http_status or '-'} | "
                    f"{item.response_time_ms or '-'} ms | {self._md(item.error_message or '-')} |"
                )
        else:
            lines.append("| - | No failed endpoints | - | - | - |")

        lines.extend([
            "",
            "## Database Changes",
            "",
            f"- Tests with database changes: {database.tests_with_db_changes}",
            f"- Tests with snapshot errors: {database.tests_with_db_errors}",
            f"- Changed tables: {', '.join(item.name for item in database.changed_tables) or '-'}",
            "",
            "| Table | Row Count Diff | Schema Changed | Sample Changed |",
            "| --- | ---: | --- | --- |",
        ])
        if database.changed_tables:
            for item in database.changed_tables:
                lines.append(
                    f"| {self._md(item.name)} | {item.row_count_diff} | "
                    f"{'yes' if item.schema_changed else 'no'} | {'yes' if item.sample_changed else 'no'} |"
                )
        else:
            lines.append("| - | 0 | no | no |")

        lines.extend([
            "",
            "## AI Smart Testing",
            "",
            f"- Plans: {ai.plan_count}",
            f"- Steps total: {ai.steps_total}",
            f"- Passed / failed / skipped / pending: {ai.steps_passed} / {ai.steps_failed} / {ai.steps_skipped} / {ai.steps_pending}",
            f"- Destructive steps: {ai.destructive_steps}",
            f"- Needs input steps: {ai.needs_input_steps}",
            "",
        ])
        if ai.analysis_summary:
            lines.extend(["### AI Analysis Summary", "", ai.analysis_summary, ""])

        lines.extend(["## Issues", ""])
        if summary.issue_list:
            for issue in summary.issue_list:
                lines.append(f"- [{issue.severity}] {issue.title}: {issue.detail}")
        else:
            lines.append("- No issues generated from current evidence.")

        lines.extend(["", "## Recommendations", ""])
        for recommendation in summary.recommendation_list:
            lines.append(f"- {recommendation.title}: {recommendation.detail}")

        lines.extend(["", "## Recent Test Runs", "", "| ID | Method | Status | HTTP | Time |", "| ---: | --- | --- | --- | ---: |"])
        if tests.recent_runs:
            for run in tests.recent_runs:
                lines.append(
                    f"| {run.id} | {run.method} | {run.status} | {run.http_status or '-'} | "
                    f"{run.response_time_ms or '-'} ms |"
                )
        else:
            lines.append("| - | - | No test runs | - | - |")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _md(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    @staticmethod
    def _loads(raw: str | None, fallback: Any) -> Any:
        if not raw:
            return fallback
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return fallback
