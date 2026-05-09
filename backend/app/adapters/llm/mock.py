import json
import re
from typing import Any

from app.adapters.llm.base import LLMClient
from app.models.llm_config import LLMConfig


class MockLLMClient(LLMClient):
    async def chat_json(
        self,
        config: LLMConfig,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        user_content = messages[-1]["content"] if messages else "{}"
        context = self._load_context(user_content)
        if context.get("mode") == "analysis":
            return {
                "analysis": "Mock analysis: results were generated from real TestRun records. Review failed steps, status codes, response bodies, and db_changes before trusting business behavior."
            }

        endpoints = context.get("endpoints") or []
        project_id = int(context.get("project", {}).get("id") or 0)
        steps = []
        for index, endpoint in enumerate(endpoints, start=1):
            method = str(endpoint.get("method", "GET")).upper()
            path = str(endpoint.get("path", ""))
            body_schema = endpoint.get("request_body_schema") if isinstance(endpoint.get("request_body_schema"), dict) else {}
            path_params = {
                name: 1
                for name in re.findall(r"{([^{}]+)}", path)
            }
            steps.append(
                {
                    "step_id": f"step-{index}",
                    "endpoint_id": int(endpoint.get("id")),
                    "method": method,
                    "path": path,
                    "purpose": f"Mock smart test for {method} {path}",
                    "path_params": path_params,
                    "query_params": self._params(endpoint.get("query_params") or []),
                    "headers": {},
                    "body": self._body_example(body_schema) if method in {"POST", "PUT", "PATCH", "DELETE"} else None,
                    "expected_status": 200,
                    "expected_response_assertions": ["Response should match the documented success shape when possible."],
                    "destructive": method in {"PUT", "PATCH", "DELETE"},
                    "requires_confirmation": method in {"PUT", "PATCH", "DELETE"},
                    "needs_user_input": False,
                    "reasoning": "Mock provider generated deterministic parameters for local workflow testing.",
                    "status": "pending",
                }
            )

        risk = "high" if any(step["destructive"] for step in steps) else "medium" if any(step["method"] == "POST" for step in steps) else "low"
        return {
            "plan_id": "mock-plan",
            "project_id": project_id,
            "scope": "single_endpoint" if len(steps) <= 1 else "selected_endpoints",
            "summary": "Mock AI test plan generated without calling an external model.",
            "risk_level": risk,
            "steps": steps,
        }

    async def test_connection(self, config: LLMConfig) -> tuple[bool, str]:
        return True, "Mock model connection succeeded."

    @staticmethod
    def _load_context(content: str) -> dict[str, Any]:
        try:
            loaded = json.loads(content)
            return loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _params(parameters: list[Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for parameter in parameters:
            if isinstance(parameter, dict) and isinstance(parameter.get("name"), str):
                result[parameter["name"]] = "string"
        return result

    def _body_example(self, schema: dict[str, Any]) -> Any:
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        properties = schema.get("properties")
        if isinstance(properties, dict):
            return {
                key: self._schema_value(value if isinstance(value, dict) else {})
                for key, value in properties.items()
            }
        return {}

    def _schema_value(self, schema: dict[str, Any]) -> Any:
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        schema_type = schema.get("type")
        if schema_type in {"integer", "number"}:
            return 1
        if schema_type == "boolean":
            return True
        if schema_type == "array":
            return []
        if schema_type == "object":
            return self._body_example(schema)
        return "string"
