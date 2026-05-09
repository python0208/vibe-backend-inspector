import json
import re
import time
from typing import Any
from urllib.parse import quote, urljoin

import httpx
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.api_endpoint import ApiEndpoint
from app.models.project import Project
from app.models.test_run import TestRun
from app.schemas.test_run import TestRequestPayload, TestRunRead
from app.services.endpoint_service import EndpointService
from app.services.project_service import ProjectService
from app.services.snapshot_service import SnapshotService


SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "proxy-authorization",
}
MAX_BODY_CHARS = 1_000_000


class TestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def run_endpoint_test(
        self,
        project_id: int,
        endpoint_id: int,
        payload: TestRequestPayload,
    ) -> TestRun:
        project = ProjectService(self.db).get_project(project_id)
        endpoint = EndpointService(self.db).get_endpoint(project_id, endpoint_id)
        method = endpoint.method.upper()
        snapshot_service = SnapshotService()
        before_snapshot = snapshot_service.capture_project_snapshot(project)

        if method not in SUPPORTED_METHODS:
            db_changes = snapshot_service.compare_snapshots(
                before_snapshot,
                snapshot_service.capture_project_snapshot(project),
            )
            return self._save_result(
                project=project,
                endpoint=endpoint,
                payload=payload,
                url=self._build_url(project.service_base_url, endpoint.path, payload.path_params),
                method=method,
                request_headers=self._build_headers(payload, has_body=False),
                status="skipped",
                http_status=None,
                response_time_ms=None,
                response_headers={},
                response_body=None,
                error_message="HTTP method is not supported in Phase 4.",
                db_changes=db_changes.model_dump(),
            )

        url = self._build_url(project.service_base_url, endpoint.path, payload.path_params)
        has_body = method in {"POST", "PUT", "PATCH", "DELETE"} and payload.json_body is not None
        headers = self._build_headers(payload, has_body=has_body)

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.request(
                    method,
                    url,
                    params=payload.query_params,
                    headers=headers,
                    json=payload.json_body if has_body else None,
                )
            response_time_ms = int((time.perf_counter() - started) * 1000)
            response_body = self._parse_response_body(response)
            status = "passed" if 200 <= response.status_code < 400 else "failed"
            db_changes = snapshot_service.compare_snapshots(
                before_snapshot,
                snapshot_service.capture_project_snapshot(project),
            )
            return self._save_result(
                project=project,
                endpoint=endpoint,
                payload=payload,
                url=url,
                method=method,
                request_headers=headers,
                status=status,
                http_status=response.status_code,
                response_time_ms=response_time_ms,
                response_headers=dict(response.headers),
                response_body=response_body,
                error_message=None,
                db_changes=db_changes.model_dump(),
            )
        except httpx.TimeoutException:
            response_time_ms = int((time.perf_counter() - started) * 1000)
            db_changes = snapshot_service.compare_snapshots(
                before_snapshot,
                snapshot_service.capture_project_snapshot(project),
            )
            return self._save_result(
                project=project,
                endpoint=endpoint,
                payload=payload,
                url=url,
                method=method,
                request_headers=headers,
                status="failed",
                http_status=None,
                response_time_ms=response_time_ms,
                response_headers={},
                response_body=None,
                error_message="Request timed out.",
                db_changes=db_changes.model_dump(),
            )
        except httpx.RequestError as exc:
            response_time_ms = int((time.perf_counter() - started) * 1000)
            db_changes = snapshot_service.compare_snapshots(
                before_snapshot,
                snapshot_service.capture_project_snapshot(project),
            )
            return self._save_result(
                project=project,
                endpoint=endpoint,
                payload=payload,
                url=url,
                method=method,
                request_headers=headers,
                status="failed",
                http_status=None,
                response_time_ms=response_time_ms,
                response_headers={},
                response_body=None,
                error_message=f"Request failed: {exc.__class__.__name__}.",
                db_changes=db_changes.model_dump(),
            )

    def list_test_runs(self, project_id: int, limit: int = 20) -> list[TestRun]:
        ProjectService(self.db).get_project(project_id)
        safe_limit = min(max(limit, 1), 100)
        return (
            self.db.query(TestRun)
            .filter(TestRun.project_id == project_id)
            .order_by(TestRun.created_at.desc(), TestRun.id.desc())
            .limit(safe_limit)
            .all()
        )

    def get_test_run(self, project_id: int, test_run_id: int) -> TestRun:
        ProjectService(self.db).get_project(project_id)
        test_run = (
            self.db.query(TestRun)
            .filter(TestRun.project_id == project_id, TestRun.id == test_run_id)
            .first()
        )
        if not test_run:
            raise NotFoundError("Test run not found.")
        return test_run

    def to_read_schema(self, test_run: TestRun) -> TestRunRead:
        return TestRunRead(
            id=test_run.id,
            project_id=test_run.project_id,
            endpoint_id=test_run.endpoint_id,
            method=test_run.method,
            url=test_run.url,
            request_headers=self._loads_dict(test_run.request_headers_json),
            request_query_params=self._loads_dict(test_run.request_query_params_json),
            request_path_params=self._loads_dict(test_run.request_path_params_json),
            request_body=self._loads_any(test_run.request_body_json),
            http_status=test_run.http_status,
            response_time_ms=test_run.response_time_ms,
            response_headers=self._loads_dict(test_run.response_headers_json),
            response_body=self._loads_any(test_run.response_body_json),
            db_changes=self._loads_dict(test_run.db_changes_json),
            status=test_run.status,
            error_message=test_run.error_message,
            created_at=test_run.created_at,
        )

    def _save_result(
        self,
        project: Project,
        endpoint: ApiEndpoint,
        payload: TestRequestPayload,
        url: str,
        method: str,
        request_headers: dict[str, str],
        status: str,
        http_status: int | None,
        response_time_ms: int | None,
        response_headers: dict[str, Any],
        response_body: Any | None,
        error_message: str | None,
        db_changes: dict[str, Any] | None = None,
    ) -> TestRun:
        test_run = TestRun(
            project_id=project.id,
            endpoint_id=endpoint.id,
            method=method,
            url=url,
            request_headers_json=self._dumps(self._mask_headers(request_headers)),
            request_query_params_json=self._dumps(payload.query_params),
            request_path_params_json=self._dumps(payload.path_params),
            request_body_json=self._dumps(self._truncate_body(payload.json_body)),
            http_status=http_status,
            response_time_ms=response_time_ms,
            response_headers_json=self._dumps(self._mask_headers(response_headers)),
            response_body_json=self._dumps(self._truncate_body(response_body)),
            db_changes_json=self._dumps(db_changes or {}),
            status=status,
            error_message=error_message,
        )
        endpoint.last_status_code = http_status
        endpoint.last_response_time_ms = response_time_ms
        endpoint.test_status = status
        self.db.add(test_run)
        self.db.commit()
        self.db.refresh(test_run)
        return test_run

    @staticmethod
    def _build_url(base_url: str, path: str, path_params: dict[str, Any]) -> str:
        missing = [
            name
            for name in re.findall(r"{([^{}]+)}", path)
            if name not in path_params or path_params[name] in (None, "")
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing path params: {joined}.")

        resolved_path = path
        for name, value in path_params.items():
            resolved_path = resolved_path.replace(f"{{{name}}}", quote(str(value), safe=""))
        return urljoin(base_url.rstrip("/") + "/", resolved_path.lstrip("/"))

    @staticmethod
    def _build_headers(payload: TestRequestPayload, has_body: bool) -> dict[str, str]:
        headers = {str(key): str(value) for key, value in payload.headers.items() if value is not None}
        if payload.bearer_token:
            headers["Authorization"] = f"Bearer {payload.bearer_token}"
        if has_body and not any(key.lower() == "content-type" for key in headers):
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _parse_response_body(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
        masked: dict[str, Any] = {}
        for key, value in headers.items():
            if key.lower() in SENSITIVE_HEADER_NAMES:
                masked[key] = "********"
            else:
                masked[key] = value
        return masked

    @classmethod
    def _truncate_body(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return value if len(value) <= MAX_BODY_CHARS else value[:MAX_BODY_CHARS] + "\n...[truncated]"
        dumped = cls._dumps(value)
        if len(dumped) <= MAX_BODY_CHARS:
            return value
        return {
            "truncated": True,
            "preview": dumped[:MAX_BODY_CHARS],
        }

    @staticmethod
    def _dumps(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    @staticmethod
    def _loads_any(raw: str | None) -> Any:
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    @classmethod
    def _loads_dict(cls, raw: str | None) -> dict[str, Any]:
        loaded = cls._loads_any(raw)
        return loaded if isinstance(loaded, dict) else {}
