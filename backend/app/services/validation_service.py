import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.api_endpoint import ApiEndpoint
from app.models.test_run import TestRun
from app.models.validation_run import ValidationRun, ValidationRunItem
from app.schemas.test_run import TestRequestPayload
from app.schemas.validation_run import (
    ValidationRunCancelResponse,
    ValidationRunCreate,
    ValidationRunDetailRead,
    ValidationRunItemRead,
    ValidationRunRead,
)
from app.services.endpoint_service import EndpointService
from app.services.project_service import ProjectService
from app.services.test_service import TestService


DESTRUCTIVE_METHODS = {"PUT", "PATCH", "DELETE"}
SUPPORTED_VALIDATION_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
DEFAULT_MAX_ENDPOINTS = 50
HARD_MAX_ENDPOINTS = 100


class ValidationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def create_and_run(self, project_id: int, payload: ValidationRunCreate) -> ValidationRun:
        ProjectService(self.db).get_project(project_id)
        endpoints = self._select_endpoints(project_id, payload)
        run = ValidationRun(
            project_id=project_id,
            name=payload.name or f"Validation Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            status="pending",
            total_count=len(endpoints),
            options_json=self._dumps(payload.model_dump()),
            summary_json="{}",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        for index, endpoint in enumerate(endpoints, start=1):
            self.db.add(
                ValidationRunItem(
                    validation_run_id=run.id,
                    project_id=project_id,
                    endpoint_id=endpoint.id,
                    method=endpoint.method.upper(),
                    path=endpoint.path,
                    status="pending",
                    order_index=index,
                )
            )
        self.db.commit()

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        self.db.commit()

        items = self.list_items(project_id, run.id)
        for item in items:
            endpoint = self.db.get(ApiEndpoint, item.endpoint_id) if item.endpoint_id else None
            if not endpoint:
                self._finish_item(item, status="failed", error_message="Endpoint no longer exists.")
                continue
            await self._run_item(item, endpoint, payload)

        self._summarize_run(run)
        return run

    def list_runs(self, project_id: int, limit: int = 20) -> list[ValidationRun]:
        ProjectService(self.db).get_project(project_id)
        safe_limit = min(max(limit, 1), 100)
        return (
            self.db.query(ValidationRun)
            .filter(ValidationRun.project_id == project_id)
            .order_by(ValidationRun.created_at.desc(), ValidationRun.id.desc())
            .limit(safe_limit)
            .all()
        )

    def get_run(self, project_id: int, run_id: int) -> ValidationRun:
        ProjectService(self.db).get_project(project_id)
        run = (
            self.db.query(ValidationRun)
            .filter(ValidationRun.project_id == project_id, ValidationRun.id == run_id)
            .first()
        )
        if not run:
            raise NotFoundError("Validation run not found.")
        return run

    def list_items(self, project_id: int, run_id: int) -> list[ValidationRunItem]:
        self.get_run(project_id, run_id)
        return (
            self.db.query(ValidationRunItem)
            .filter(
                ValidationRunItem.project_id == project_id,
                ValidationRunItem.validation_run_id == run_id,
            )
            .order_by(ValidationRunItem.order_index.asc(), ValidationRunItem.id.asc())
            .all()
        )

    def cancel_run(self, project_id: int, run_id: int) -> ValidationRunCancelResponse:
        run = self.get_run(project_id, run_id)
        if run.status in {"completed", "failed", "cancelled"}:
            return ValidationRunCancelResponse(
                ok=False,
                message="Validation run is already finished.",
                run=self.to_read_schema(run),
            )
        run.status = "cancelled"
        run.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(run)
        return ValidationRunCancelResponse(
            ok=True,
            message="Validation run cancelled.",
            run=self.to_read_schema(run),
        )

    def to_read_schema(self, run: ValidationRun) -> ValidationRunRead:
        return ValidationRunRead(
            id=run.id,
            project_id=run.project_id,
            name=run.name,
            status=run.status,
            total_count=run.total_count,
            passed_count=run.passed_count,
            failed_count=run.failed_count,
            skipped_count=run.skipped_count,
            warning_count=run.warning_count,
            started_at=run.started_at,
            finished_at=run.finished_at,
            options=self._loads(run.options_json, {}),
            summary=self._loads(run.summary_json, {}),
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    def to_detail_schema(self, run: ValidationRun) -> ValidationRunDetailRead:
        base = self.to_read_schema(run).model_dump()
        return ValidationRunDetailRead(
            **base,
            items=[self.to_item_schema(item) for item in self.list_items(run.project_id, run.id)],
        )

    def to_item_schema(self, item: ValidationRunItem) -> ValidationRunItemRead:
        test_run = self.db.get(TestRun, item.test_run_id) if item.test_run_id else None
        request_preview = self._request_preview(item, test_run)
        db_changes = self._loads(test_run.db_changes_json, {}) if test_run else {}
        response_body = self._loads(test_run.response_body_json, None) if test_run else None
        failure_category = self._failure_category(item, test_run)
        failure_reason = self._failure_reason(item, test_run, failure_category)
        return ValidationRunItemRead(
            id=item.id,
            validation_run_id=item.validation_run_id,
            project_id=item.project_id,
            endpoint_id=item.endpoint_id,
            test_run_id=item.test_run_id,
            method=item.method,
            path=item.path,
            status=item.status,
            http_status=item.http_status,
            response_time_ms=item.response_time_ms,
            error_message=item.error_message,
            db_change_status=item.db_change_status,
            request_headers=request_preview["headers"],
            request_query_params=request_preview["query_params"],
            request_path_params=request_preview["path_params"],
            request_body=request_preview["body"],
            response_body_summary=response_body,
            db_changes=db_changes if isinstance(db_changes, dict) else {},
            failure_category=failure_category,
            failure_reason=failure_reason,
            suggestion=self._suggestion(failure_category),
            order_index=item.order_index,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _select_endpoints(self, project_id: int, payload: ValidationRunCreate) -> list[ApiEndpoint]:
        endpoint_service = EndpointService(self.db)
        endpoints = endpoint_service.list_endpoints(project_id)
        if payload.endpoint_ids:
            wanted = set(payload.endpoint_ids)
            endpoints = [endpoint for endpoint in endpoints if endpoint.id in wanted]

        allowed_methods = self._allowed_methods(payload)
        endpoints = [endpoint for endpoint in endpoints if endpoint.method.upper() in allowed_methods]
        max_endpoints = min(payload.max_endpoints or DEFAULT_MAX_ENDPOINTS, HARD_MAX_ENDPOINTS)
        return endpoints[:max_endpoints]

    @staticmethod
    def _allowed_methods(payload: ValidationRunCreate) -> set[str]:
        if payload.methods:
            return {method.upper() for method in payload.methods}
        allowed: set[str] = set()
        if payload.include_get:
            allowed.add("GET")
        if payload.include_post:
            allowed.add("POST")
        if payload.include_put_patch_delete:
            allowed.update(DESTRUCTIVE_METHODS)
        return allowed

    async def _run_item(
        self,
        item: ValidationRunItem,
        endpoint: ApiEndpoint,
        options: ValidationRunCreate,
    ) -> None:
        item.status = "running"
        self.db.commit()

        skip_reason = self._skip_reason(endpoint, options)
        if skip_reason:
            self._finish_item(item, status="skipped", error_message=skip_reason)
            return

        try:
            request_payload = self._build_payload(endpoint)
        except ValueError as exc:
            self._finish_item(item, status="skipped", error_message=str(exc))
            return

        try:
            test_run = await TestService(self.db).run_endpoint_test(
                item.project_id,
                endpoint.id,
                request_payload,
            )
            self._apply_test_run(item, test_run)
        except Exception as exc:  # noqa: BLE001 - a single endpoint must not stop the batch.
            self._finish_item(
                item,
                status="failed",
                error_message=f"Endpoint validation failed: {exc.__class__.__name__}.",
            )

    @staticmethod
    def _skip_reason(endpoint: ApiEndpoint, options: ValidationRunCreate) -> str | None:
        method = endpoint.method.upper()
        if method not in SUPPORTED_VALIDATION_METHODS:
            return "HTTP method is not supported for validation."
        if method in DESTRUCTIVE_METHODS and (options.skip_destructive or not options.include_put_patch_delete):
            return "Skipped destructive method by default."
        if endpoint.auth_required:
            return "Auth required; batch validation needs user-provided credentials."
        if endpoint.source == "manual" and method in {"POST", "PUT", "PATCH"}:
            schema = ValidationService._loads(endpoint.request_body_schema_json, {})
            if not schema:
                return "Manual endpoint needs a request body schema or user input."
        return None

    def _build_payload(self, endpoint: ApiEndpoint) -> TestRequestPayload:
        method = endpoint.method.upper()
        path_params = self._values_from_params(
            self._loads(endpoint.path_params_json, []),
            required_only=False,
        )
        for name in re.findall(r"{([^{}]+)}", endpoint.path):
            path_params.setdefault(name, self._example_for_name(name))
        query_params = self._values_from_params(
            self._loads(endpoint.query_params_json, []),
            required_only=True,
        )
        body = None
        if method in {"POST", "PUT", "PATCH"}:
            body_schema = self._loads(endpoint.request_body_schema_json, {})
            if not body_schema:
                raise ValueError("Request body schema is missing; needs user input.")
            body = self._example_from_schema(body_schema)
        return TestRequestPayload(
            path_params=path_params,
            query_params=query_params,
            headers={},
            bearer_token=None,
            json_body=body,
        )

    def _values_from_params(self, params: Any, required_only: bool) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if not isinstance(params, list):
            return values
        for param in params:
            if not isinstance(param, dict):
                continue
            if required_only and not param.get("required"):
                continue
            name = param.get("name")
            if not name:
                continue
            schema = param.get("schema") if isinstance(param.get("schema"), dict) else {}
            values[str(name)] = self._example_from_schema(schema, str(name))
        return values

    def _example_from_schema(self, schema: Any, fallback_name: str | None = None) -> Any:
        if not isinstance(schema, dict):
            return self._example_for_name(fallback_name or "value")
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
            return schema["enum"][0]
        schema_type = schema.get("type")
        if not schema_type and "properties" in schema:
            schema_type = "object"

        if schema_type == "object":
            properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
            required = set(schema.get("required") if isinstance(schema.get("required"), list) else [])
            keys = required or set(properties.keys())
            return {
                key: self._example_from_schema(properties.get(key, {}), str(key))
                for key in keys
            }
        if schema_type == "array":
            return [self._example_from_schema(schema.get("items", {}), fallback_name)]
        if schema_type in {"integer", "number"}:
            return 1
        if schema_type == "boolean":
            return True
        return self._example_for_name(fallback_name or "value")

    @staticmethod
    def _example_for_name(name: str) -> Any:
        lowered = name.lower()
        if lowered == "uuid" or lowered.endswith("_uuid"):
            return "00000000-0000-4000-8000-000000000001"
        if lowered == "id" or lowered.endswith("_id") or lowered.endswith("id"):
            return 1
        if "email" in lowered:
            return "test@example.com"
        if "name" in lowered:
            return "validation-test"
        return "test"

    def _apply_test_run(self, item: ValidationRunItem, test_run: TestRun) -> None:
        db_changes = self._loads(test_run.db_changes_json, {})
        item.test_run_id = test_run.id
        item.status = test_run.status
        item.http_status = test_run.http_status
        item.response_time_ms = test_run.response_time_ms
        item.error_message = test_run.error_message
        item.db_change_status = str(db_changes.get("status")) if isinstance(db_changes, dict) else None
        self.db.commit()
        self.db.refresh(item)

    def _request_preview(self, item: ValidationRunItem, test_run: TestRun | None) -> dict[str, Any]:
        if test_run:
            return {
                "headers": self._loads(test_run.request_headers_json, {}),
                "query_params": self._loads(test_run.request_query_params_json, {}),
                "path_params": self._loads(test_run.request_path_params_json, {}),
                "body": self._loads(test_run.request_body_json, None),
            }

        endpoint = self.db.get(ApiEndpoint, item.endpoint_id) if item.endpoint_id else None
        if not endpoint:
            return {"headers": {}, "query_params": {}, "path_params": {}, "body": None}
        try:
            payload = self._build_payload(endpoint)
            return {
                "headers": payload.headers,
                "query_params": payload.query_params,
                "path_params": payload.path_params,
                "body": payload.json_body,
            }
        except ValueError:
            path_params = {
                name: self._example_for_name(name)
                for name in re.findall(r"{([^{}]+)}", endpoint.path)
            }
            return {"headers": {}, "query_params": {}, "path_params": path_params, "body": None}

    def _failure_category(self, item: ValidationRunItem, test_run: TestRun | None) -> str | None:
        if item.status == "passed":
            return None
        message = (item.error_message or "").lower()
        if item.status == "skipped":
            if "destructive" in message:
                return "skipped_safety"
            if "auth required" in message or "credentials" in message:
                return "auth_required"
            if "needs" in message or "missing" in message or "schema" in message:
                return "needs_user_input"
            return "unknown"

        http_status = item.http_status if item.http_status is not None else test_run.http_status if test_run else None
        if http_status in {400, 422}:
            return "validation_error"
        if http_status == 401:
            return "auth_required"
        if http_status == 403:
            return "permission_denied"
        if http_status == 404:
            return "not_found"
        if http_status is not None and http_status >= 500:
            return "server_error"
        if "request failed" in message or "connecterror" in message or "timeout" in message or "timed out" in message:
            return "network_error"
        return "unknown"

    @staticmethod
    def _failure_reason(
        item: ValidationRunItem,
        test_run: TestRun | None,
        category: str | None,
    ) -> str | None:
        if not category:
            return None
        if item.error_message:
            return item.error_message
        http_status = item.http_status if item.http_status is not None else test_run.http_status if test_run else None
        if http_status is not None:
            return f"HTTP {http_status} returned during validation."
        return "Validation did not complete successfully."

    @staticmethod
    def _suggestion(category: str | None) -> str | None:
        suggestions = {
            "validation_error": "Review generated parameters and required schema fields; this endpoint may need more realistic input.",
            "auth_required": "Provide valid credentials or run this endpoint from the single Test Runner with an auth token.",
            "permission_denied": "Check account permissions and authorization rules for this endpoint.",
            "not_found": "Verify the path and generated IDs; this endpoint may require an existing business record.",
            "server_error": "Inspect backend logs and reproduce the request with the shown generated parameters.",
            "skipped_safety": "The endpoint was skipped by safety defaults. Enable destructive methods only against a test backend.",
            "needs_user_input": "Add request schema details or run this endpoint manually with real business parameters.",
            "network_error": "Confirm the service base URL is running and reachable from the local agent.",
            "unknown": "Open the linked TestRun or run the endpoint manually to inspect the raw response.",
        }
        return suggestions.get(category) if category else None

    def _finish_item(
        self,
        item: ValidationRunItem,
        status: str,
        error_message: str | None = None,
    ) -> None:
        item.status = status
        item.error_message = error_message
        self.db.commit()
        self.db.refresh(item)

    def _summarize_run(self, run: ValidationRun) -> None:
        items = self.list_items(run.project_id, run.id)
        counts = Counter(item.status for item in items)
        warning_count = sum(1 for item in items if item.db_change_status == "error")
        total = len(items)
        pass_rate = round((counts["passed"] / total) * 100, 1) if total else 0
        run.status = "completed"
        run.total_count = total
        run.passed_count = counts["passed"]
        run.failed_count = counts["failed"]
        run.skipped_count = counts["skipped"]
        run.warning_count = warning_count
        run.finished_at = datetime.now(timezone.utc)
        run.summary_json = self._dumps(
            {
                "pass_rate": pass_rate,
                "db_change_error_count": warning_count,
                "needs_input_count": sum(
                    1 for item in items if item.error_message and "needs" in item.error_message.lower()
                ),
            }
        )
        self.db.commit()
        self.db.refresh(run)

    @staticmethod
    def _dumps(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    @staticmethod
    def _loads(raw: str | None, fallback: Any) -> Any:
        if not raw:
            return fallback
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return fallback
