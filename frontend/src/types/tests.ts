export type TestRunStatus = "passed" | "failed" | "skipped";
export type DbChangesStatus = "captured" | "skipped" | "error";

export interface RowCountDiff {
  before: number;
  after: number;
  diff: number;
}

export interface TableSchemaDiff {
  columns_added: string[];
  columns_removed: string[];
  columns_changed: string[];
}

export interface TableSampleDiff {
  before: Record<string, unknown>[];
  after: Record<string, unknown>[];
}

export interface DbChanges {
  status: DbChangesStatus | string;
  changed: boolean;
  tables_added: string[];
  tables_removed: string[];
  tables_modified: string[];
  row_count_diff: Record<string, RowCountDiff>;
  schema_diff: Record<string, TableSchemaDiff>;
  sample_diff: Record<string, TableSampleDiff>;
  warning_message?: string | null;
}

export interface TestRequestPayload {
  path_params: Record<string, unknown>;
  query_params: Record<string, unknown>;
  headers: Record<string, string>;
  bearer_token?: string | null;
  json_body?: unknown;
}

export interface TestRun {
  id: number;
  project_id: number;
  endpoint_id: number;
  method: string;
  url: string;
  request_headers: Record<string, unknown>;
  request_query_params: Record<string, unknown>;
  request_path_params: Record<string, unknown>;
  request_body?: unknown;
  http_status?: number | null;
  response_time_ms?: number | null;
  response_headers: Record<string, unknown>;
  response_body?: unknown;
  db_changes: DbChanges;
  status: TestRunStatus | string;
  error_message?: string | null;
  created_at: string;
}
