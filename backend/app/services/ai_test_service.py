import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.ai_test_plan import AITestPlanRecord, AITestStepRecord
from app.models.api_endpoint import ApiEndpoint
from app.schemas.ai_test import (
    AITestAnalysisResponse,
    AITestPlan,
    AITestPlanGenerateRequest,
    AITestPlanGenerateResponse,
    AITestPlanRead,
    AITestStep,
    AITestStepExecuteResponse,
)
from app.schemas.test_run import TestRequestPayload
from app.services.database_service import DatabaseService
from app.services.endpoint_service import EndpointService
from app.services.llm_config_service import LLMConfigService
from app.services.llm_service import LLMService
from app.services.project_service import ProjectService
from app.services.test_service import TestService


DESTRUCTIVE_METHODS = {"PUT", "PATCH", "DELETE"}
SENSITIVE_KEYS = ("authorization", "password", "token", "secret", "credential", "api_key")


class AITestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def generate_plan(
        self,
        project_id: int,
        payload: AITestPlanGenerateRequest,
    ) -> AITestPlanGenerateResponse:
        project = ProjectService(self.db).get_project(project_id)
        llm_config = LLMConfigService(self.db).get_config(payload.llm_config_id)
        endpoints = self._resolve_endpoints(project_id, payload.endpoint_ids)
        context = self._build_planning_context(project, endpoints)
        messages = self._planning_messages(context)
        raw_plan = await LLMService().chat_json(llm_config, messages, {})
        plan = self._validate_plan(raw_plan, project_id, endpoints, payload.scope)
        plan_id = f"plan-{uuid4().hex[:12]}"
        plan.plan_id = plan_id
        self._scope_step_ids(plan, plan_id)
        record = AITestPlanRecord(
            id=plan_id,
            project_id=project_id,
            llm_config_id=llm_config.id,
            scope=plan.scope,
            summary=plan.summary,
            risk_level=plan.risk_level,
            plan_json=plan.model_dump_json(),
        )
        self.db.add(record)
        for step in plan.steps:
            self.db.add(
                AITestStepRecord(
                    id=step.step_id,
                    plan_id=plan_id,
                    project_id=project_id,
                    endpoint_id=step.endpoint_id,
                    status=step.status,
                    step_json=step.model_dump_json(),
                    result_test_run_id=step.result_test_run_id,
                )
            )
        self.db.commit()
        self.db.refresh(record)
        return AITestPlanGenerateResponse(
            ok=True,
            message="AI test plan generated.",
            plan=self.to_read_schema(record),
        )

    def list_plans(self, project_id: int) -> list[AITestPlanRead]:
        ProjectService(self.db).get_project(project_id)
        records = (
            self.db.query(AITestPlanRecord)
            .filter(AITestPlanRecord.project_id == project_id)
            .order_by(AITestPlanRecord.updated_at.desc(), AITestPlanRecord.created_at.desc())
            .limit(20)
            .all()
        )
        return [self.to_read_schema(record) for record in records]

    def get_plan(self, project_id: int, plan_id: str) -> AITestPlanRead:
        return self.to_read_schema(self._get_plan_record(project_id, plan_id))

    async def execute_step(
        self,
        project_id: int,
        plan_id: str,
        step_id: str,
        confirmed: bool,
    ) -> AITestStepExecuteResponse:
        record = self._get_plan_record(project_id, plan_id)
        step_record = self._get_step_record(project_id, plan_id, step_id)
        step = AITestStep.model_validate(json.loads(step_record.step_json))

        if step.needs_user_input:
            step.status = "skipped"
            step.ai_explanation = "Step requires user input before execution."
            self._save_step(step_record, step)
            self._sync_plan(record, step)
            return AITestStepExecuteResponse(
                ok=False,
                message="Step requires user input.",
                plan=self.to_read_schema(record),
                step=step,
                test_run=None,
            )

        if self._is_destructive(step) and not confirmed:
            return AITestStepExecuteResponse(
                ok=False,
                message="This step requires confirmation before execution.",
                plan=self.to_read_schema(record),
                step=step,
                test_run=None,
            )

        step.status = "running"
        self._save_step(step_record, step)
        test_payload = TestRequestPayload(
            path_params=step.path_params,
            query_params=step.query_params,
            headers=step.headers,
            bearer_token=None,
            json_body=step.body,
        )
        test_service = TestService(self.db)
        test_run = await test_service.run_endpoint_test(project_id, step.endpoint_id, test_payload)
        test_run_read = test_service.to_read_schema(test_run)
        step.result_test_run_id = test_run.id
        step.status = "passed" if test_run.status == "passed" else "failed"
        step.ai_explanation = self._local_step_explanation(step, test_run_read.model_dump())
        self._save_step(step_record, step)
        self._sync_plan(record, step)
        return AITestStepExecuteResponse(
            ok=True,
            message="Step executed.",
            plan=self.to_read_schema(record),
            step=step,
            test_run=test_run_read,
        )

    async def analyze_plan(self, project_id: int, plan_id: str) -> AITestAnalysisResponse:
        record = self._get_plan_record(project_id, plan_id)
        config = LLMConfigService(self.db).get_config(record.llm_config_id)
        plan = AITestPlan.model_validate(json.loads(record.plan_json))
        runs = TestService(self.db).list_test_runs(project_id, limit=20)
        context = {
            "mode": "analysis",
            "plan": plan.model_dump(),
            "test_runs": [
                TestService(self.db).to_read_schema(run).model_dump(mode="json")
                for run in runs
                if run.id in {step.result_test_run_id for step in plan.steps if step.result_test_run_id}
            ],
        }
        raw = await LLMService().chat_json(
            config,
            self._analysis_messages(context),
            {"type": "object", "properties": {"analysis": {"type": "string"}}},
        )
        analysis = str(raw.get("analysis") or "No AI analysis returned.")
        record.analysis_json = json.dumps({"analysis": analysis}, ensure_ascii=False)
        self.db.commit()
        self.db.refresh(record)
        return AITestAnalysisResponse(
            ok=True,
            message="AI analysis generated.",
            analysis=analysis,
            plan=self.to_read_schema(record),
        )

    def to_read_schema(self, record: AITestPlanRecord) -> AITestPlanRead:
        plan = AITestPlan.model_validate(json.loads(record.plan_json))
        analysis = None
        if record.analysis_json:
            try:
                loaded = json.loads(record.analysis_json)
                analysis = loaded.get("analysis") if isinstance(loaded, dict) else None
            except json.JSONDecodeError:
                analysis = None
        return AITestPlanRead(
            **plan.model_dump(),
            llm_config_id=record.llm_config_id,
            analysis=analysis,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _resolve_endpoints(self, project_id: int, endpoint_ids: list[int]) -> list[ApiEndpoint]:
        endpoint_service = EndpointService(self.db)
        if not endpoint_ids:
            endpoints = endpoint_service.list_endpoints(project_id)
            return endpoints[:1]
        return [endpoint_service.get_endpoint(project_id, endpoint_id) for endpoint_id in endpoint_ids]

    def _build_planning_context(self, project: Any, endpoints: list[ApiEndpoint]) -> dict[str, Any]:
        schema_response = DatabaseService().inspect_project_database(project)
        database_summary: dict[str, Any] = {
            "ok": schema_response.ok,
            "message": schema_response.message,
            "tables": [],
        }
        if schema_response.database_schema:
            database_summary = {
                "ok": True,
                "database_type": schema_response.database_schema.database_type,
                "database_name": schema_response.database_schema.database_name,
                "tables": [
                    {
                        "name": table.name,
                        "row_count": table.row_count,
                        "columns": [column.model_dump() for column in table.columns[:12]],
                        "sample_rows": [self._mask_sensitive(row) for row in table.sample_rows[:3]],
                    }
                    for table in schema_response.database_schema.tables[:12]
                ],
            }
        recent_runs = [
            TestService(self.db).to_read_schema(run).model_dump(mode="json")
            for run in TestService(self.db).list_test_runs(project.id, limit=5)
        ]
        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "service_base_url": project.service_base_url,
                "database_type": project.database_type,
            },
            "endpoints": [self._endpoint_context(endpoint) for endpoint in endpoints],
            "database_schema_summary": database_summary,
            "recent_test_runs": recent_runs,
        }

    @staticmethod
    def _endpoint_context(endpoint: ApiEndpoint) -> dict[str, Any]:
        return {
            "id": endpoint.id,
            "method": endpoint.method,
            "path": endpoint.path,
            "summary": endpoint.summary,
            "description": endpoint.description,
            "query_params": AITestService._loads(endpoint.query_params_json, []),
            "path_params": AITestService._loads(endpoint.path_params_json, []),
            "request_body_schema": AITestService._loads(endpoint.request_body_schema_json, {}),
            "response_schema": AITestService._loads(endpoint.response_schema_json, {}),
            "auth_required": endpoint.auth_required,
        }

    @staticmethod
    def _planning_messages(context: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are Vibe Backend Inspector's Smart API Testing Agent. Your mission is to inspect "
                    "OpenAPI endpoint metadata, request/response schemas, database summaries, and recent "
                    "test runs, then produce a safe executable API test plan. Return only JSON. The top-level "
                    "object must contain summary, risk_level, and steps. Each step must contain step_id, "
                    "endpoint_id, method, path, purpose, path_params, query_params, headers, body, "
                    "expected_status, expected_response_assertions, destructive, requires_confirmation, "
                    "needs_user_input, reasoning, and status. Do not execute HTTP requests, do not modify "
                    "code, do not invent execution results, and do not include secrets. Mark PUT, PATCH, "
                    "and DELETE as destructive and requires_confirmation. If parameters cannot be inferred, "
                    "set needs_user_input true instead of guessing."
                ),
            },
            {"role": "user", "content": json.dumps(context, ensure_ascii=False, default=str)},
        ]

    @staticmethod
    def _analysis_messages(context: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "Analyze real API test results. Return only JSON with an analysis string. "
                    "Use status codes, response bodies, and db_changes as facts."
                ),
            },
            {"role": "user", "content": json.dumps(context, ensure_ascii=False, default=str)},
        ]

    def _validate_plan(
        self,
        raw_plan: dict[str, Any],
        project_id: int,
        endpoints: list[ApiEndpoint],
        scope: str,
    ) -> AITestPlan:
        endpoint_by_id = {endpoint.id: endpoint for endpoint in endpoints}
        raw_plan = self._normalize_llm_plan(raw_plan, endpoints)
        raw_plan["project_id"] = project_id
        raw_plan["scope"] = scope
        raw_plan.setdefault("plan_id", "pending")
        plan = AITestPlan.model_validate(raw_plan)
        validated_steps: list[AITestStep] = []
        for index, step in enumerate(plan.steps, start=1):
            endpoint = endpoint_by_id.get(step.endpoint_id)
            if not endpoint:
                raise ValueError(f"AI plan referenced endpoint outside the selected project: {step.endpoint_id}.")
            step.step_id = step.step_id or f"step-{index}"
            step.method = endpoint.method.upper()
            step.path = endpoint.path
            if self._is_destructive(step):
                step.destructive = True
                step.requires_confirmation = True
            step.headers = self._mask_sensitive(step.headers)
            step.status = "pending"
            validated_steps.append(step)
        if not validated_steps:
            raise ValueError("AI plan must contain at least one step.")
        plan.steps = validated_steps
        plan.risk_level = self._risk_level(validated_steps)
        return plan

    @staticmethod
    def _scope_step_ids(plan: AITestPlan, plan_id: str) -> None:
        scoped_steps: list[AITestStep] = []
        for index, step in enumerate(plan.steps, start=1):
            raw_step_id = step.step_id or f"step-{index}"
            if not raw_step_id.startswith(f"{plan_id}-"):
                step.step_id = f"{plan_id}-{raw_step_id}-{index}"
            scoped_steps.append(step)
        plan.steps = scoped_steps

    def _normalize_llm_plan(
        self,
        raw_plan: dict[str, Any],
        endpoints: list[ApiEndpoint],
    ) -> dict[str, Any]:
        candidate = raw_plan
        for wrapper_key in ("test_plan", "plan", "ai_test_plan", "data", "result"):
            wrapped = candidate.get(wrapper_key)
            if isinstance(wrapped, dict):
                candidate = wrapped
                break

        steps_value = (
            candidate.get("steps")
            or candidate.get("test_steps")
            or candidate.get("test_cases")
            or candidate.get("testCases")
            or candidate.get("api_tests")
            or candidate.get("requests")
            or candidate.get("actions")
            or candidate.get("cases")
            or []
        )
        if not steps_value:
            steps_value = self._find_step_list(candidate)
        if isinstance(steps_value, dict):
            steps_value = list(steps_value.values())
        if not isinstance(steps_value, list):
            steps_value = []

        normalized_steps = [
            self._normalize_llm_step(step, index, endpoints)
            for index, step in enumerate(steps_value, start=1)
            if isinstance(step, dict)
        ]

        used_fallback = False
        if not normalized_steps:
            used_fallback = True
            normalized_steps = [
                self._fallback_step(endpoint, index)
                for index, endpoint in enumerate(endpoints, start=1)
            ]

        default_summary = (
            "Smart API testing agent generated a fallback plan because the model returned no executable steps."
            if used_fallback
            else "AI-generated API test plan."
        )
        return {
            "plan_id": candidate.get("plan_id") or candidate.get("id") or "pending",
            "summary": candidate.get("summary")
            or candidate.get("description")
            or candidate.get("objective")
            or default_summary,
            "risk_level": self._normalize_risk(candidate.get("risk_level") or candidate.get("risk") or "medium"),
            "steps": normalized_steps,
        }

    def _normalize_llm_step(
        self,
        raw_step: dict[str, Any],
        index: int,
        endpoints: list[ApiEndpoint],
    ) -> dict[str, Any]:
        endpoint = self._match_endpoint(raw_step, endpoints) or endpoints[min(index - 1, len(endpoints) - 1)]
        method = str(raw_step.get("method") or endpoint.method).upper()
        body = (
            raw_step.get("body")
            if "body" in raw_step
            else raw_step.get("request_body")
            if "request_body" in raw_step
            else raw_step.get("json_body")
        )
        destructive = method in DESTRUCTIVE_METHODS or bool(raw_step.get("destructive"))
        return {
            "step_id": str(raw_step.get("step_id") or raw_step.get("id") or f"step-{index}"),
            "endpoint_id": int(raw_step.get("endpoint_id") or endpoint.id),
            "method": method,
            "path": str(raw_step.get("path") or endpoint.path),
            "purpose": str(
                raw_step.get("purpose")
                or raw_step.get("name")
                or raw_step.get("description")
                or raw_step.get("test_case")
                or f"AI-generated test for {method} {endpoint.path}"
            ),
            "path_params": self._object_or_empty(raw_step.get("path_params") or raw_step.get("path_parameters")),
            "query_params": self._object_or_empty(raw_step.get("query_params") or raw_step.get("query_parameters")),
            "headers": self._string_dict(raw_step.get("headers")),
            "body": body,
            "expected_status": self._normalize_expected_status(
                raw_step.get("expected_status")
                or raw_step.get("expected_status_code")
                or raw_step.get("expected_http_status")
            ),
            "expected_response_assertions": self._string_list(
                raw_step.get("expected_response_assertions")
                or raw_step.get("assertions")
                or raw_step.get("expected_result")
            ),
            "destructive": destructive,
            "requires_confirmation": destructive or bool(raw_step.get("requires_confirmation")),
            "needs_user_input": bool(raw_step.get("needs_user_input")),
            "reasoning": str(raw_step.get("reasoning") or raw_step.get("rationale") or ""),
            "status": "pending",
        }

    @staticmethod
    def _find_step_list(value: Any) -> list[Any]:
        if isinstance(value, list) and any(isinstance(item, dict) for item in value):
            dict_items = [item for item in value if isinstance(item, dict)]
            if any("method" in item or "endpoint_id" in item or "path" in item for item in dict_items):
                return dict_items
        if isinstance(value, dict):
            for item in value.values():
                found = AITestService._find_step_list(item)
                if found:
                    return found
        return []

    @staticmethod
    def _fallback_step(endpoint: ApiEndpoint, index: int) -> dict[str, Any]:
        import re

        method = endpoint.method.upper()
        destructive = method in DESTRUCTIVE_METHODS
        return {
            "step_id": f"fallback-step-{index}",
            "endpoint_id": endpoint.id,
            "method": method,
            "path": endpoint.path,
            "purpose": (
                "Fallback executable step generated by the backend because the model response "
                "did not contain valid test steps."
            ),
            "path_params": {name: 1 for name in re.findall(r"{([^{}]+)}", endpoint.path)},
            "query_params": {},
            "headers": {},
            "body": None,
            "expected_status": 200,
            "expected_response_assertions": [
                "Review the actual response manually because the model did not provide assertions."
            ],
            "destructive": destructive,
            "requires_confirmation": destructive,
            "needs_user_input": destructive,
            "reasoning": "Backend fallback: LLM output had no usable steps.",
            "status": "pending",
        }

    @staticmethod
    def _match_endpoint(raw_step: dict[str, Any], endpoints: list[ApiEndpoint]) -> ApiEndpoint | None:
        endpoint_id = raw_step.get("endpoint_id")
        if endpoint_id is not None:
            for endpoint in endpoints:
                if str(endpoint.id) == str(endpoint_id):
                    return endpoint
        method = str(raw_step.get("method") or "").upper()
        path = str(raw_step.get("path") or "")
        for endpoint in endpoints:
            if endpoint.method.upper() == method and endpoint.path == path:
                return endpoint
        return None

    @staticmethod
    def _normalize_risk(value: Any) -> str:
        normalized = str(value).lower()
        if normalized in {"low", "medium", "high"}:
            return normalized
        if normalized in {"safe", "read"}:
            return "low"
        if normalized in {"danger", "destructive"}:
            return "high"
        return "medium"

    @staticmethod
    def _object_or_empty(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _string_dict(value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {}
        return {str(key): str(item) for key, item in value.items() if item is not None}

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if value is None:
            return []
        return [str(value)]

    @staticmethod
    def _normalize_expected_status(value: Any) -> int | None:
        if value is None:
            return None
        try:
            status = int(value)
        except (TypeError, ValueError):
            return None
        return status if 100 <= status <= 599 else None

    def _get_plan_record(self, project_id: int, plan_id: str) -> AITestPlanRecord:
        record = (
            self.db.query(AITestPlanRecord)
            .filter(AITestPlanRecord.project_id == project_id, AITestPlanRecord.id == plan_id)
            .first()
        )
        if not record:
            raise NotFoundError("AI test plan not found.")
        return record

    def _get_step_record(self, project_id: int, plan_id: str, step_id: str) -> AITestStepRecord:
        record = (
            self.db.query(AITestStepRecord)
            .filter(
                AITestStepRecord.project_id == project_id,
                AITestStepRecord.plan_id == plan_id,
                AITestStepRecord.id == step_id,
            )
            .first()
        )
        if not record:
            raise NotFoundError("AI test step not found.")
        return record

    def _save_step(self, record: AITestStepRecord, step: AITestStep) -> None:
        record.status = step.status
        record.result_test_run_id = step.result_test_run_id
        record.step_json = step.model_dump_json()
        self.db.commit()
        self.db.refresh(record)

    def _sync_plan(self, record: AITestPlanRecord, updated_step: AITestStep) -> None:
        plan = AITestPlan.model_validate(json.loads(record.plan_json))
        plan.steps = [
            updated_step if step.step_id == updated_step.step_id else step
            for step in plan.steps
        ]
        record.summary = plan.summary
        record.risk_level = plan.risk_level
        record.plan_json = plan.model_dump_json()
        self.db.commit()
        self.db.refresh(record)

    @staticmethod
    def _is_destructive(step: AITestStep) -> bool:
        return step.method.upper() in DESTRUCTIVE_METHODS or step.destructive

    @staticmethod
    def _risk_level(steps: list[AITestStep]) -> str:
        if any(step.method.upper() in DESTRUCTIVE_METHODS for step in steps):
            return "high"
        if any(step.method.upper() == "POST" for step in steps):
            return "medium"
        return "low"

    @staticmethod
    def _local_step_explanation(step: AITestStep, test_run: dict[str, Any]) -> str:
        status = test_run.get("status")
        http_status = test_run.get("http_status")
        db_changes = test_run.get("db_changes", {})
        return (
            f"Executed {step.method} {step.path}. Test status: {status}; "
            f"HTTP status: {http_status}; DB changes: {db_changes.get('status', 'unknown')}."
        )

    @classmethod
    def _mask_sensitive(cls, value: dict[str, Any]) -> dict[str, Any]:
        masked: dict[str, Any] = {}
        for key, item in value.items():
            if any(marker in key.lower() for marker in SENSITIVE_KEYS):
                masked[key] = "********" if item is not None else None
            else:
                masked[key] = item
        return masked

    @staticmethod
    def _loads(raw: str | None, fallback: Any) -> Any:
        if not raw:
            return fallback
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return fallback
