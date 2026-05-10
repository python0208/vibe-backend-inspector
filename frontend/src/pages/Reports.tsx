import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Database,
  Download,
  FileText,
  RefreshCw,
  Sparkles,
  XCircle
} from "lucide-react";

import { downloadReportMarkdown, generateReport, getLatestReport, getReportSummary } from "../api/reports";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type { PageKey } from "../types/navigation";
import type { ProjectListItem } from "../types/project";
import type { Report, ReportIssue, ReportSummary } from "../types/report";

interface ReportsProps {
  t: Messages;
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  onNavigate: (page: PageKey) => void;
}

export function Reports({ t, projects, selectedProjectId, onNavigate }: ReportsProps) {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [latestReport, setLatestReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null;
  const activeReport = latestReport ?? summary;

  async function refreshReports(projectId: number) {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, latestData] = await Promise.all([
        getReportSummary(projectId),
        getLatestReport(projectId)
      ]);
      setSummary(summaryData);
      setLatestReport(latestData.report ?? null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.reports.loadFailed);
      setSummary(null);
      setLatestReport(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (selectedProjectId) {
      void refreshReports(selectedProjectId);
    } else {
      setSummary(null);
      setLatestReport(null);
    }
  }, [selectedProjectId]);

  const hasEvidence = Boolean(
    summary && (
      summary.endpoint_summary.total > 0 ||
      summary.test_summary.total_runs > 0 ||
      summary.ai_test_summary.plan_count > 0 ||
      summary.validation_run_summary.total_count > 0
    )
  );
  const canExport = Boolean(selectedProjectId && latestReport);

  async function handleGenerate() {
    if (!selectedProjectId) return;
    setGenerating(true);
    setError(null);
    try {
      const report = await generateReport(selectedProjectId);
      setLatestReport(report);
      setSummary(report);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.reports.loadFailed);
    } finally {
      setGenerating(false);
    }
  }

  async function handleExportMarkdown() {
    if (!selectedProjectId || !latestReport) return;
    try {
      const blob = await downloadReportMarkdown(selectedProjectId, latestReport.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `vibe-report-${latestReport.id}.md`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.reports.exportFailed);
    }
  }

  if (!selectedProjectId || !selectedProject) {
    return (
      <section className="page-stack">
        <PageHeader subtitle={t.placeholders.reportsSubtitle} title={t.placeholders.reportsTitle} />
        <div className="empty-panel">
          <strong>{t.reports.noProjectTitle}</strong>
          <p>{t.reports.noProjectDescription}</p>
          <button className="primary-button" onClick={() => onNavigate("setup")} type="button">
            {t.dashboard.configureProject}
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <PageHeader
        actions={
          <div className="button-row">
            <button className="ghost-button" disabled={loading} onClick={() => refreshReports(selectedProject.id)} type="button">
              <RefreshCw size={16} />
              {t.common.refresh}
            </button>
            <button className="outline-button" disabled={!canExport} onClick={handleExportMarkdown} type="button">
              <Download size={16} />
              {t.reports.exportMarkdown}
            </button>
            <button className="primary-button" disabled={generating} onClick={handleGenerate} type="button">
              {generating ? <span className="button-spinner" /> : <FileText size={16} />}
              {generating ? t.reports.generating : t.reports.generate}
            </button>
          </div>
        }
        subtitle={t.placeholders.reportsSubtitle}
        title={t.placeholders.reportsTitle}
      />

      {error ? <div className="notice danger">{error}</div> : null}
      {!latestReport && hasEvidence ? (
        <div className="notice info">
          <strong>{t.reports.summaryOnly}</strong>
          <span>{t.reports.noReportDescription}</span>
        </div>
      ) : null}
      {!loading && !hasEvidence ? (
        <div className="empty-panel">
          <strong>{t.reports.noReportTitle}</strong>
          <p>{t.reports.noReportDescription}</p>
          <div className="button-row">
            <button className="primary-button" onClick={() => onNavigate("testRunner")} type="button">
              {t.nav.testRunner}
            </button>
            <button className="outline-button" onClick={() => onNavigate("apiMap")} type="button">
              {t.nav.apiMap}
            </button>
          </div>
        </div>
      ) : null}

      {activeReport ? (
        <>
          <ReportStats report={activeReport} t={t} />
          <div className="reports-overview-grid">
            <Card className="report-score-panel">
              <div className="card-heading">
                <div>
                  <h2>{t.reports.overallScore}</h2>
                  <p>{latestReport ? `${t.reports.generatedAt}: ${formatDate(latestReport.generated_at)}` : t.reports.summaryOnly}</p>
                </div>
                <StatusBadge tone={riskTone(activeReport.risk_level)}>{activeReport.risk_level}</StatusBadge>
              </div>
              <div className="score-big">{activeReport.overall_score}<span>/100</span></div>
            </Card>
            <Card>
              <div className="card-heading">
                <div>
                  <h2>{t.reports.issues}</h2>
                  <p>{t.reports.latestReport}</p>
                </div>
                <StatusBadge tone={activeReport.issue_list.length ? "warning" : "success"}>
                  {activeReport.issue_list.length}
                </StatusBadge>
              </div>
              <IssueList issues={activeReport.issue_list.slice(0, 4)} t={t} />
            </Card>
          </div>
          <div className="reports-detail-grid">
            <FailedEndpointsTable report={activeReport} t={t} />
            <DatabaseChangesPanel report={activeReport} t={t} />
            <AITestSummaryPanel report={activeReport} t={t} />
            <ValidationRunSummaryPanel report={activeReport} t={t} />
            <RecommendationsPanel report={activeReport} t={t} />
          </div>
        </>
      ) : loading ? (
        <div className="empty-panel">{t.reports.loading}</div>
      ) : null}
    </section>
  );
}

function ReportStats({ report, t }: { report: ReportSummary; t: Messages }) {
  const endpoints = report.endpoint_summary;
  const tests = report.test_summary;
  const database = report.database_change_summary;
  const ai = report.ai_test_summary;
  const validation = report.validation_run_summary;
  return (
    <div className="stat-grid five">
      <StatCard icon={BarChart3} title={t.reports.endpointsTested} value={`${endpoints.tested}/${endpoints.total}`} hint={`${endpoints.pass_rate}%`} tone="blue" />
      <StatCard icon={CheckCircle2} title={t.reports.passRate} value={`${endpoints.pass_rate}%`} hint={`${endpoints.passed} ${t.common.success}`} tone="green" />
      <StatCard icon={XCircle} title={t.reports.failedCount} value={tests.failed_runs} hint={`${tests.server_error_count} 5xx / ${tests.validation_error_count} 422`} tone="red" />
      <StatCard icon={Database} title={t.reports.databaseChanges} value={database.changed_tables.length} hint={`${database.tests_with_db_changes} runs`} tone="purple" />
      <StatCard icon={Sparkles} title={t.reports.aiSmartSteps} value={ai.steps_total} hint={`${ai.steps_passed}/${ai.steps_failed}/${ai.steps_skipped}`} tone="orange" />
      <StatCard icon={BarChart3} title={t.testRunner.validationRun} value={validation.total_count} hint={`${validation.pass_rate}%`} tone="blue" />
    </div>
  );
}

function FailedEndpointsTable({ report, t }: { report: ReportSummary; t: Messages }) {
  const failed = report.test_summary.failed_endpoints;
  return (
    <Card className="report-panel wide">
      <SectionHeading count={failed.length} title={t.reports.failedEndpoints} />
      {failed.length === 0 ? (
        <div className="empty-panel compact">{t.reports.noFailedEndpoints}</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>{t.apiMap.method}</th>
              <th>{t.apiMap.path}</th>
              <th>{t.apiMap.lastStatus}</th>
              <th>{t.apiMap.latency}</th>
              <th>{t.common.error}</th>
            </tr>
          </thead>
          <tbody>
            {failed.map((item) => (
              <tr key={`${item.test_run_id}-${item.path}`}>
                <td><StatusBadge tone="neutral">{item.method}</StatusBadge></td>
                <td><code>{item.path}</code></td>
                <td><StatusBadge tone={item.http_status && item.http_status >= 500 ? "danger" : "warning"}>{item.http_status ?? "-"}</StatusBadge></td>
                <td>{item.response_time_ms ?? "-"} ms</td>
                <td>{item.error_message ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}

function DatabaseChangesPanel({ report, t }: { report: ReportSummary; t: Messages }) {
  const database = report.database_change_summary;
  return (
    <Card className="report-panel">
      <SectionHeading count={database.changed_tables.length} title={t.reports.databaseChangesSummary} />
      {database.changed_tables.length === 0 ? (
        <div className="empty-panel compact">{t.testRunner.noDatabaseChanges}</div>
      ) : (
        <div className="report-change-list">
          {database.changed_tables.map((table) => (
            <div className="report-change-row" key={table.name}>
              <div>
                <strong>{table.name}</strong>
                <span>{t.testRunner.rowCountChanges}: {table.row_count_diff}</span>
              </div>
              <div className="button-row">
                {table.schema_changed ? <StatusBadge tone="warning">{t.testRunner.schemaChanges}</StatusBadge> : null}
                {table.sample_changed ? <StatusBadge tone="info">{t.testRunner.sampleChanges}</StatusBadge> : null}
              </div>
            </div>
          ))}
        </div>
      )}
      {database.tests_with_db_errors ? (
        <div className="notice danger">{t.testRunner.databaseChangesError}: {database.tests_with_db_errors}</div>
      ) : null}
    </Card>
  );
}

function AITestSummaryPanel({ report, t }: { report: ReportSummary; t: Messages }) {
  const ai = report.ai_test_summary;
  return (
    <Card className="report-panel">
      <SectionHeading count={ai.plan_count} title={t.reports.aiSmartTestSummary} />
      {ai.plan_count === 0 ? (
        <div className="empty-panel compact">{t.aiTest.noPlan}</div>
      ) : (
        <div className="report-ai-grid">
          <Metric label={t.aiTest.steps} value={ai.steps_total} />
          <Metric label={t.common.success} value={ai.steps_passed} />
          <Metric label={t.common.error} value={ai.steps_failed} />
          <Metric label={t.testRunner.skipped} value={ai.steps_skipped} />
          <Metric label={t.aiTest.destructive} value={ai.destructive_steps} />
          <Metric label={t.aiTest.needsInput} value={ai.needs_input_steps} />
        </div>
      )}
      {ai.analysis_summary ? (
        <div className="report-analysis">
          <strong>{t.aiTest.analysis}</strong>
          <p>{ai.analysis_summary}</p>
        </div>
      ) : null}
    </Card>
  );
}

function ValidationRunSummaryPanel({ report, t }: { report: ReportSummary; t: Messages }) {
  const validation = report.validation_run_summary;
  return (
    <Card className="report-panel">
      <SectionHeading count={validation.total_count} title={t.testRunner.validationRun} />
      {validation.latest_run_id ? (
        <div className="report-ai-grid">
          <div><span>{t.testRunner.total}</span><strong>{validation.total_count}</strong></div>
          <div><span>{t.testRunner.passed}</span><strong>{validation.passed_count}</strong></div>
          <div><span>{t.testRunner.failed}</span><strong>{validation.failed_count}</strong></div>
          <div><span>{t.testRunner.skipped}</span><strong>{validation.skipped_count}</strong></div>
          <div><span>{t.reports.passRate}</span><strong>{validation.pass_rate}%</strong></div>
          <div><span>{t.apiMap.testStatus}</span><strong>{validation.status ?? "-"}</strong></div>
        </div>
      ) : (
        <div className="empty-panel compact">{t.testRunner.noValidationRuns}</div>
      )}
    </Card>
  );
}

function RecommendationsPanel({ report, t }: { report: ReportSummary; t: Messages }) {
  return (
    <Card className="report-panel wide">
      <SectionHeading count={report.recommendation_list.length} title={t.reports.recommendations} />
      <div className="recommendation-list">
        {report.recommendation_list.map((recommendation) => (
          <div className="recommendation-item" key={`${recommendation.category}-${recommendation.title}`}>
            <StatusBadge tone="info">{recommendation.category}</StatusBadge>
            <div>
              <strong>{recommendation.title}</strong>
              <p>{recommendation.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function IssueList({ issues, t }: { issues: ReportIssue[]; t: Messages }) {
  if (issues.length === 0) {
    return <div className="empty-panel compact">{t.reports.noIssues}</div>;
  }
  return (
    <div className="issue-list">
      {issues.map((issue) => (
        <div className="issue-item" key={`${issue.category}-${issue.title}-${issue.test_run_id ?? ""}`}>
          <StatusBadge tone={severityTone(issue.severity)}>{issue.severity}</StatusBadge>
          <div>
            <strong>{issue.title}</strong>
            <p>{issue.detail}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function SectionHeading({ count, title }: { count: number; title: string }) {
  return (
    <div className="card-heading">
      <h2>{title}</h2>
      <StatusBadge tone="neutral">{count}</StatusBadge>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-pill">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function riskTone(risk: string): StatusTone {
  if (risk === "high") return "danger";
  if (risk === "medium") return "warning";
  return "success";
}

function severityTone(severity: string): StatusTone {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "info";
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}
