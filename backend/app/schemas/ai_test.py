from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.test_run import TestRunRead


AITestScope = Literal["single_endpoint", "selected_endpoints"]
AITestRiskLevel = Literal["low", "medium", "high"]
AITestStepStatus = Literal["pending", "running", "passed", "failed", "skipped"]


class AITestStep(BaseModel):
    step_id: str
    endpoint_id: int
    method: str
    path: str
    purpose: str
    path_params: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None
    expected_status: int | None = None
    expected_response_assertions: list[str] = Field(default_factory=list)
    destructive: bool = False
    requires_confirmation: bool = False
    needs_user_input: bool = False
    reasoning: str = ""
    status: AITestStepStatus = "pending"
    result_test_run_id: int | None = None
    ai_explanation: str | None = None


class AITestPlan(BaseModel):
    plan_id: str
    project_id: int
    scope: AITestScope
    summary: str
    risk_level: AITestRiskLevel
    steps: list[AITestStep] = Field(default_factory=list)


class AITestPlanGenerateRequest(BaseModel):
    llm_config_id: int
    endpoint_ids: list[int] = Field(default_factory=list)
    scope: AITestScope = "single_endpoint"


class AITestPlanRead(AITestPlan):
    llm_config_id: int
    analysis: str | None = None
    created_at: datetime
    updated_at: datetime


class AITestPlanGenerateResponse(BaseModel):
    ok: bool
    message: str
    plan: AITestPlanRead | None = None


class AITestStepExecuteRequest(BaseModel):
    confirmed: bool = False


class AITestStepExecuteResponse(BaseModel):
    ok: bool
    message: str
    plan: AITestPlanRead
    step: AITestStep
    test_run: TestRunRead | None = None


class AITestAnalysisResponse(BaseModel):
    ok: bool
    message: str
    analysis: str | None = None
    plan: AITestPlanRead
