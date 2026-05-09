import { apiRequest } from "./client";
import type { DatabaseInspectResponse, DatabaseProjectConnectionTestResponse } from "../types/database";

export function inspectDatabase(projectId: number): Promise<DatabaseInspectResponse> {
  return apiRequest<DatabaseInspectResponse>(`/api/projects/${projectId}/database/inspect`, {
    method: "POST"
  });
}

export function getDatabaseSchema(projectId: number): Promise<DatabaseInspectResponse> {
  return apiRequest<DatabaseInspectResponse>(`/api/projects/${projectId}/database/schema`);
}

export function testProjectDatabaseConnection(
  projectId: number
): Promise<DatabaseProjectConnectionTestResponse> {
  return apiRequest<DatabaseProjectConnectionTestResponse>(
    `/api/projects/${projectId}/database/test-connection`,
    { method: "POST" }
  );
}
