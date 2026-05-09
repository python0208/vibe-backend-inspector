import { apiRequest } from "./client";
import type { TestRequestPayload, TestRun } from "../types/tests";

export function runEndpointTest(
  projectId: number,
  endpointId: number,
  payload: TestRequestPayload
): Promise<TestRun> {
  return apiRequest<TestRun>(`/api/projects/${projectId}/endpoints/${endpointId}/test`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listTestRuns(projectId: number, limit = 20): Promise<TestRun[]> {
  return apiRequest<TestRun[]>(`/api/projects/${projectId}/test-runs?limit=${limit}`);
}

export function getTestRun(projectId: number, testRunId: number): Promise<TestRun> {
  return apiRequest<TestRun>(`/api/projects/${projectId}/test-runs/${testRunId}`);
}
