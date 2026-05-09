import type { TestRun } from "./tests";

export type AITestScope = "single_endpoint" | "selected_endpoints";
export type AITestRiskLevel = "low" | "medium" | "high";
export type AITestStepStatus = "pending" | "running" | "passed" | "failed" | "skipped";

export interface AITestStep {
  step_id: string;
  endpoint_id: number;
  method: string;
  path: string;
  purpose: string;
  path_params: Record<string, unknown>;
  query_params: Record<string, unknown>;
  headers: Record<string, string>;
  body?: unknown;
  expected_status?: number | null;
  expected_response_assertions: string[];
  destructive: boolean;
  requires_confirmation: boolean;
  needs_user_input: boolean;
  reasoning: string;
  status: AITestStepStatus | string;
  result_test_run_id?: number | null;
  ai_explanation?: string | null;
}

export interface AITestPlan {
  plan_id: string;
  project_id: number;
  llm_config_id: number;
  scope: AITestScope;
  summary: string;
  risk_level: AITestRiskLevel;
  steps: AITestStep[];
  analysis?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AITestPlanGenerateResponse {
  ok: boolean;
  message: string;
  plan?: AITestPlan | null;
}

export interface AITestStepExecuteResponse {
  ok: boolean;
  message: string;
  plan: AITestPlan;
  step: AITestStep;
  test_run?: TestRun | null;
}

export interface AITestAnalysisResponse {
  ok: boolean;
  message: string;
  analysis?: string | null;
  plan: AITestPlan;
}
