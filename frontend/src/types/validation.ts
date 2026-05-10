import type { HttpMethod } from "./api";

export type ValidationRunStatus = "pending" | "running" | "completed" | "failed" | "cancelled";
export type ValidationRunItemStatus = "pending" | "running" | "passed" | "failed" | "skipped";
export type ValidationFailureCategory =
  | "validation_error"
  | "auth_required"
  | "permission_denied"
  | "not_found"
  | "server_error"
  | "skipped_safety"
  | "needs_user_input"
  | "network_error"
  | "unknown";

export interface ValidationRunCreatePayload {
  name?: string | null;
  endpoint_ids: number[];
  methods: HttpMethod[];
  skip_destructive: boolean;
  include_get: boolean;
  include_post: boolean;
  include_put_patch_delete: boolean;
  use_ai_generated_params: boolean;
  max_endpoints?: number | null;
}

export interface ValidationRunItem {
  id: number;
  validation_run_id: number;
  project_id: number;
  endpoint_id?: number | null;
  test_run_id?: number | null;
  method: string;
  path: string;
  status: ValidationRunItemStatus | string;
  http_status?: number | null;
  response_time_ms?: number | null;
  error_message?: string | null;
  db_change_status?: string | null;
  request_headers: Record<string, unknown>;
  request_query_params: Record<string, unknown>;
  request_path_params: Record<string, unknown>;
  request_body?: unknown;
  response_body_summary?: unknown;
  db_changes: Record<string, unknown>;
  failure_category?: ValidationFailureCategory | string | null;
  failure_reason?: string | null;
  suggestion?: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface ValidationRun {
  id: number;
  project_id: number;
  name: string;
  status: ValidationRunStatus | string;
  total_count: number;
  passed_count: number;
  failed_count: number;
  skipped_count: number;
  warning_count: number;
  started_at?: string | null;
  finished_at?: string | null;
  options: Record<string, unknown>;
  summary: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ValidationRunDetail extends ValidationRun {
  items: ValidationRunItem[];
}

export interface ValidationRunCancelResponse {
  ok: boolean;
  message: string;
  run: ValidationRun;
}
