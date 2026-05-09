import { apiRequest } from "./client";
import type {
  AITestAnalysisResponse,
  AITestPlan,
  AITestPlanGenerateResponse,
  AITestScope,
  AITestStepExecuteResponse
} from "../types/aiTest";

export function generateAITestPlan(
  projectId: number,
  llmConfigId: number,
  endpointIds: number[],
  scope: AITestScope
): Promise<AITestPlanGenerateResponse> {
  return apiRequest<AITestPlanGenerateResponse>(`/api/projects/${projectId}/ai-tests/plans`, {
    method: "POST",
    body: JSON.stringify({
      llm_config_id: llmConfigId,
      endpoint_ids: endpointIds,
      scope
    })
  });
}

export function listAITestPlans(projectId: number): Promise<AITestPlan[]> {
  return apiRequest<AITestPlan[]>(`/api/projects/${projectId}/ai-tests/plans`);
}

export function executeAITestStep(
  projectId: number,
  planId: string,
  stepId: string,
  confirmed: boolean
): Promise<AITestStepExecuteResponse> {
  return apiRequest<AITestStepExecuteResponse>(
    `/api/projects/${projectId}/ai-tests/plans/${planId}/execute-step/${stepId}`,
    {
      method: "POST",
      body: JSON.stringify({ confirmed })
    }
  );
}

export function analyzeAITestPlan(projectId: number, planId: string): Promise<AITestAnalysisResponse> {
  return apiRequest<AITestAnalysisResponse>(`/api/projects/${projectId}/ai-tests/plans/${planId}/analyze`, {
    method: "POST"
  });
}
