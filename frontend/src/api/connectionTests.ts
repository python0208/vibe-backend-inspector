import { apiRequest } from "./client";
import type { ConnectionTestResult, DatabaseType } from "../types/project";

export function testOpenApi(url: string): Promise<ConnectionTestResult> {
  return apiRequest<ConnectionTestResult>("/api/connection-tests/openapi", {
    method: "POST",
    body: JSON.stringify({ url })
  });
}

export function testDatabase(
  databaseType: DatabaseType,
  databaseConfig: Record<string, unknown>
): Promise<ConnectionTestResult> {
  return apiRequest<ConnectionTestResult>("/api/connection-tests/database", {
    method: "POST",
    body: JSON.stringify({
      database_type: databaseType,
      database_config: databaseConfig
    })
  });
}
