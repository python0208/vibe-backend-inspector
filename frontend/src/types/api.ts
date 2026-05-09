export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "OPTIONS" | "HEAD";
export type TestStatus = "untested" | "passed" | "failed" | "skipped";

export interface Endpoint {
  id: number;
  project_id: number;
  method: HttpMethod | string;
  path: string;
  summary?: string | null;
  description?: string | null;
  operation_id?: string | null;
  tags: string[];
  query_params: Record<string, unknown>[];
  path_params: Record<string, unknown>[];
  request_body_schema: Record<string, unknown>;
  response_schema: Record<string, unknown>;
  auth_required: boolean;
  source: string;
  test_status: TestStatus | string;
  last_status_code?: number | null;
  last_response_time_ms?: number | null;
  created_at: string;
  updated_at: string;
}

export interface EndpointDiscoveryResult {
  ok: boolean;
  message: string;
  project_id: number;
  openapi_url?: string | null;
  total_endpoints: number;
  created: number;
  updated: number;
  attempted_urls: string[];
}
