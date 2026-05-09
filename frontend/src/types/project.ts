export type DatabaseType = "none" | "sqlite" | "mysql" | "postgres";
export type AuthType = "none" | "bearer" | "basic" | "custom_headers";

export interface AuthConfig {
  type: AuthType;
  token?: string | null;
  username?: string | null;
  password?: string | null;
  headers?: Record<string, string>;
}

export interface ProjectPayload {
  name: string;
  project_path: string;
  service_base_url: string;
  openapi_url?: string | null;
  database_type: DatabaseType;
  database_config: Record<string, unknown>;
  auth_config: AuthConfig;
}

export interface Project extends ProjectPayload {
  id: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectListItem {
  id: number;
  name: string;
  project_path: string;
  service_base_url: string;
  openapi_url?: string | null;
  database_type: DatabaseType;
  created_at: string;
  updated_at: string;
}

export interface ConnectionTestResult {
  ok: boolean;
  status_code?: number | null;
  message: string;
  detected_format?: string | null;
  title?: string | null;
  database_type?: DatabaseType;
}
