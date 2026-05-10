import { apiRequest } from "./client";
import type {
  ValidationRun,
  ValidationRunCancelResponse,
  ValidationRunCreatePayload,
  ValidationRunDetail,
  ValidationRunItem
} from "../types/validation";

export function createValidationRun(
  projectId: number,
  payload: ValidationRunCreatePayload
): Promise<ValidationRunDetail> {
  return apiRequest<ValidationRunDetail>(`/api/projects/${projectId}/validation-runs`, {
    body: JSON.stringify(payload),
    method: "POST"
  });
}

export function listValidationRuns(projectId: number, limit = 10): Promise<ValidationRun[]> {
  return apiRequest<ValidationRun[]>(`/api/projects/${projectId}/validation-runs?limit=${limit}`);
}

export function getValidationRun(projectId: number, runId: number): Promise<ValidationRunDetail> {
  return apiRequest<ValidationRunDetail>(`/api/projects/${projectId}/validation-runs/${runId}`);
}

export function listValidationRunItems(projectId: number, runId: number): Promise<ValidationRunItem[]> {
  return apiRequest<ValidationRunItem[]>(`/api/projects/${projectId}/validation-runs/${runId}/items`);
}

export function cancelValidationRun(projectId: number, runId: number): Promise<ValidationRunCancelResponse> {
  return apiRequest<ValidationRunCancelResponse>(`/api/projects/${projectId}/validation-runs/${runId}/cancel`, {
    method: "POST"
  });
}
