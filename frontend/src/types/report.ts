import type { TestRun } from "./tests";

export type RiskLevel = "low" | "medium" | "high";
export type IssueSeverity = "low" | "medium" | "high";

export interface EndpointSummary {
  total: number;
  tested: number;
  passed: number;
  failed: number;
  skipped: number;
  untested: number;
  pass_rate: number;
}

export interface FailedEndpointReportItem {
  endpoint_id?: number | null;
  test_run_id?: number | null;
  method: string;
  path: string;
  summary?: string | null;
  http_status?: number | null;
  response_time_ms?: number | null;
  error_message?: string | null;
  created_at?: string | null;
}

export interface TestSummary {
  total_runs: number;
  recent_runs: TestRun[];
  passed_runs: number;
  failed_runs: number;
  skipped_runs: number;
  average_response_time_ms?: number | null;
  validation_error_count: number;
  server_error_count: number;
  destructive_run_count: number;
  failed_endpoints: FailedEndpointReportItem[];
}

export interface RowCountAggregate {
  before?: number | null;
  after?: number | null;
  diff: number;
}

export interface DatabaseChangedTableItem {
  name: string;
  row_count_diff: number;
  schema_changed: boolean;
  sample_changed: boolean;
}

export interface DatabaseChangeSummary {
  tests_with_db_changes: number;
  tests_with_db_errors: number;
  changed_tables: DatabaseChangedTableItem[];
  tables_added: string[];
  tables_removed: string[];
  tables_modified: string[];
  row_count_diff: Record<string, RowCountAggregate>;
  schema_diff: Record<string, Record<string, string[]>>;
  warnings: string[];
}

export interface AITestSummary {
  plan_count: number;
  latest_plan_id?: string | null;
  steps_total: number;
  steps_passed: number;
  steps_failed: number;
  steps_skipped: number;
  steps_pending: number;
  destructive_steps: number;
  needs_input_steps: number;
  analysis_summary?: string | null;
  risk_levels: Record<string, number>;
}

export interface ValidationRunSummary {
  latest_run_id?: number | null;
  name?: string | null;
  status?: string | null;
  total_count: number;
  passed_count: number;
  failed_count: number;
  skipped_count: number;
  warning_count: number;
  pass_rate: number;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface ReportIssue {
  severity: IssueSeverity | string;
  category: string;
  title: string;
  detail: string;
  endpoint_id?: number | null;
  test_run_id?: number | null;
  method?: string | null;
  path?: string | null;
}

export interface ReportRecommendation {
  category: string;
  title: string;
  detail: string;
  related_issue_category?: string | null;
}

export interface ReportSummary {
  project_id: number;
  project_name: string;
  title: string;
  generated_at: string;
  overall_score: number;
  risk_level: RiskLevel | string;
  endpoint_summary: EndpointSummary;
  test_summary: TestSummary;
  database_change_summary: DatabaseChangeSummary;
  ai_test_summary: AITestSummary;
  validation_run_summary: ValidationRunSummary;
  issue_list: ReportIssue[];
  recommendation_list: ReportRecommendation[];
}

export interface Report extends ReportSummary {
  id: number;
  markdown_content: string;
}

export interface LatestReportResponse {
  ok: boolean;
  message: string;
  report?: Report | null;
}
