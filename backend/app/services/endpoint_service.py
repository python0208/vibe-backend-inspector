import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.api_endpoint import ApiEndpoint
from app.schemas.api_endpoint import EndpointRead, EndpointUpsertPayload


class EndpointService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_endpoints(self, project_id: int) -> list[ApiEndpoint]:
        return (
            self.db.query(ApiEndpoint)
            .filter(ApiEndpoint.project_id == project_id)
            .order_by(ApiEndpoint.path.asc(), ApiEndpoint.method.asc())
            .all()
        )

    def get_endpoint(self, project_id: int, endpoint_id: int) -> ApiEndpoint:
        endpoint = (
            self.db.query(ApiEndpoint)
            .filter(ApiEndpoint.project_id == project_id, ApiEndpoint.id == endpoint_id)
            .first()
        )
        if not endpoint:
            raise NotFoundError("Endpoint not found.")
        return endpoint

    def upsert_endpoints(
        self,
        project_id: int,
        payloads: list[EndpointUpsertPayload],
    ) -> tuple[int, int, list[ApiEndpoint]]:
        existing = {
            (endpoint.method.upper(), endpoint.path): endpoint
            for endpoint in self.list_endpoints(project_id)
        }
        created = 0
        updated = 0
        endpoints: list[ApiEndpoint] = []

        for payload in payloads:
            key = (payload.method.upper(), payload.path)
            endpoint = existing.get(key)
            if endpoint:
                updated += 1
                self._apply_payload(endpoint, payload)
            else:
                created += 1
                endpoint = ApiEndpoint(project_id=project_id)
                self._apply_payload(endpoint, payload)
                self.db.add(endpoint)
            endpoints.append(endpoint)

        self.db.commit()
        for endpoint in endpoints:
            self.db.refresh(endpoint)
        return created, updated, endpoints

    def to_read_schema(self, endpoint: ApiEndpoint) -> EndpointRead:
        return EndpointRead(
            id=endpoint.id,
            project_id=endpoint.project_id,
            method=endpoint.method,
            path=endpoint.path,
            summary=endpoint.summary,
            description=endpoint.description,
            operation_id=endpoint.operation_id,
            tags=self._loads_list(endpoint.tags_json),
            query_params=self._loads_list(endpoint.query_params_json),
            path_params=self._loads_list(endpoint.path_params_json),
            request_body_schema=self._loads_dict(endpoint.request_body_schema_json),
            response_schema=self._loads_dict(endpoint.response_schema_json),
            auth_required=endpoint.auth_required,
            source=endpoint.source,
            test_status=endpoint.test_status,
            last_status_code=endpoint.last_status_code,
            last_response_time_ms=endpoint.last_response_time_ms,
            created_at=endpoint.created_at,
            updated_at=endpoint.updated_at,
        )

    @staticmethod
    def _apply_payload(endpoint: ApiEndpoint, payload: EndpointUpsertPayload) -> None:
        endpoint.method = payload.method.upper()
        endpoint.path = payload.path
        endpoint.summary = payload.summary
        endpoint.description = payload.description
        endpoint.operation_id = payload.operation_id
        endpoint.tags_json = json.dumps(payload.tags)
        endpoint.query_params_json = json.dumps(payload.query_params)
        endpoint.path_params_json = json.dumps(payload.path_params)
        endpoint.request_body_schema_json = json.dumps(payload.request_body_schema)
        endpoint.response_schema_json = json.dumps(payload.response_schema)
        endpoint.auth_required = payload.auth_required
        endpoint.source = payload.source

    @staticmethod
    def _loads_dict(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            loaded = json.loads(raw)
            return loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _loads_list(raw: str | None) -> list[Any]:
        if not raw:
            return []
        try:
            loaded = json.loads(raw)
            return loaded if isinstance(loaded, list) else []
        except json.JSONDecodeError:
            return []
