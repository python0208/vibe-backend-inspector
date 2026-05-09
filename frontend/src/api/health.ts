import { apiRequest } from "./client";
import type { HealthResponse } from "../types/health";

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}
