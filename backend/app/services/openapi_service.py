import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx
import yaml
from sqlalchemy.orm import Session

from app.schemas.connection import OpenApiTestResponse
from app.models.project import Project
from app.schemas.api_endpoint import EndpointUpsertPayload, OpenApiDiscoveryResponse
from app.services.endpoint_service import EndpointService


COMMON_OPENAPI_PATHS = [
    "/openapi.json",
    "/swagger.json",
    "/v3/api-docs",
    "/api-docs",
    "/docs-json",
]
MAX_OPENAPI_FILE_BYTES = 2 * 1024 * 1024
OPENAPI_FILE_EXTENSIONS = {".json", ".yaml", ".yml"}


@dataclass
class FetchedOpenApiDocument:
    url: str
    payload: dict[str, Any]
    detected_format: str


class OpenApiFileImportError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class OpenApiService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    async def test_url(self, url: str) -> OpenApiTestResponse:
        document, error = await self.fetch_document(url)
        if error:
            return OpenApiTestResponse(
                ok=False,
                status_code=error.get("status_code"),
                message=error["message"],
            )

        title = None
        if isinstance(document.payload.get("info"), dict):
            title = document.payload["info"].get("title")

        return OpenApiTestResponse(
            ok=True,
            status_code=200,
            message="OpenAPI document is reachable.",
            detected_format=document.detected_format,
            title=title,
        )

    async def fetch_document(
        self,
        url: str,
    ) -> tuple[FetchedOpenApiDocument | None, dict[str, Any] | None]:
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                response = await client.get(url)
        except httpx.RequestError as exc:
            return None, {"message": f"OpenAPI document is not reachable: {exc.__class__.__name__}."}

        if response.status_code >= 400:
            return None, {
                "status_code": response.status_code,
                "message": "OpenAPI document is not reachable.",
            }

        try:
            payload = response.json()
        except ValueError:
            return None, {
                "status_code": response.status_code,
                "message": "Response is reachable but is not valid JSON.",
            }

        if not isinstance(payload, dict):
            return None, {
                "status_code": response.status_code,
                "message": "Response JSON must be an object.",
            }

        detected_format = None
        if "openapi" in payload:
            detected_format = "openapi"
        elif "swagger" in payload:
            detected_format = "swagger"

        if not detected_format:
            return None, {
                "status_code": response.status_code,
                "message": "JSON is reachable but does not look like OpenAPI or Swagger.",
            }

        return FetchedOpenApiDocument(url=url, payload=payload, detected_format=detected_format), None

    async def discover_from_project(self, project: Project) -> OpenApiDiscoveryResponse:
        if not self.db:
            raise RuntimeError("Database session is required for discovery.")
        if not project.openapi_url:
            return OpenApiDiscoveryResponse(
                ok=False,
                message="Project does not have an OpenAPI URL.",
                project_id=project.id,
            )

        document, error = await self.fetch_document(project.openapi_url)
        if error or not document:
            return OpenApiDiscoveryResponse(
                ok=False,
                message=error["message"] if error else "OpenAPI discovery failed.",
                project_id=project.id,
                openapi_url=project.openapi_url,
            )

        return self._save_document(project, document)

    async def auto_detect_and_discover(self, project: Project) -> OpenApiDiscoveryResponse:
        if not self.db:
            raise RuntimeError("Database session is required for discovery.")

        attempted_urls: list[str] = []
        for path in COMMON_OPENAPI_PATHS:
            candidate_url = self._join_url(project.service_base_url, path)
            attempted_urls.append(candidate_url)
            document, _ = await self.fetch_document(candidate_url)
            if document:
                project.openapi_url = document.url
                self.db.commit()
                self.db.refresh(project)
                result = self._save_document(project, document)
                result.attempted_urls = attempted_urls
                return result

        return OpenApiDiscoveryResponse(
            ok=False,
            message="No OpenAPI document was detected.",
            project_id=project.id,
            attempted_urls=attempted_urls,
        )

    def import_document_file(
        self,
        project: Project,
        filename: str,
        content: bytes,
    ) -> OpenApiDiscoveryResponse:
        if not self.db:
            raise RuntimeError("Database session is required for discovery.")

        document = self.parse_uploaded_document(filename, content)
        payloads = self.parse_endpoints(document.payload, source="openapi_file")
        if not payloads:
            raise OpenApiFileImportError("OpenAPI document does not contain supported endpoints.")

        created, updated, _ = EndpointService(self.db).upsert_endpoints(project.id, payloads)
        return OpenApiDiscoveryResponse(
            ok=True,
            message="OpenAPI file imported.",
            project_id=project.id,
            total_endpoints=len(payloads),
            created=created,
            updated=updated,
        )

    def parse_uploaded_document(self, filename: str, content: bytes) -> FetchedOpenApiDocument:
        if len(content) > MAX_OPENAPI_FILE_BYTES:
            raise OpenApiFileImportError("OpenAPI file is too large.", status_code=413)
        if not content or not content.strip():
            raise OpenApiFileImportError("OpenAPI file is empty.")

        extension = self._file_extension(filename)
        if extension not in OPENAPI_FILE_EXTENSIONS:
            raise OpenApiFileImportError("Only JSON, YAML, or YML OpenAPI files are supported.")

        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise OpenApiFileImportError("OpenAPI file must be UTF-8 encoded.") from exc

        try:
            if extension == ".json":
                payload = json.loads(text)
            else:
                payload = yaml.safe_load(text)
        except json.JSONDecodeError as exc:
            raise OpenApiFileImportError(f"OpenAPI JSON format error: {exc.msg}.") from exc
        except yaml.YAMLError as exc:
            raise OpenApiFileImportError(f"OpenAPI YAML format error: {exc.__class__.__name__}.") from exc

        if not isinstance(payload, dict):
            raise OpenApiFileImportError("OpenAPI document must be a JSON/YAML object.")

        detected_format = self._detect_format(payload)
        if not detected_format:
            raise OpenApiFileImportError("Unsupported OpenAPI structure.")

        paths = payload.get("paths")
        if not isinstance(paths, dict) or not paths:
            raise OpenApiFileImportError("OpenAPI document is missing paths.")

        return FetchedOpenApiDocument(url=filename, payload=payload, detected_format=detected_format)

    def parse_endpoints(self, document: dict[str, Any], source: str = "openapi") -> list[EndpointUpsertPayload]:
        paths = document.get("paths")
        if not isinstance(paths, dict):
            return []

        global_security = document.get("security")
        endpoints: list[EndpointUpsertPayload] = []
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            path_level_parameters = self._as_list(path_item.get("parameters"))
            for raw_method, operation in path_item.items():
                method = raw_method.upper()
                if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                    continue
                if not isinstance(operation, dict):
                    continue

                parameters = path_level_parameters + self._as_list(operation.get("parameters"))
                query_params = [self._clean_parameter(param) for param in parameters if param.get("in") == "query"]
                path_params = [self._clean_parameter(param) for param in parameters if param.get("in") == "path"]
                response_schema = self._extract_response_schema(operation.get("responses"))

                endpoints.append(
                    EndpointUpsertPayload(
                        method=method,
                        path=str(path),
                        summary=operation.get("summary"),
                        description=operation.get("description"),
                        operation_id=operation.get("operationId"),
                        tags=[
                            str(tag)
                            for tag in self._as_list(operation.get("tags"))
                            if isinstance(tag, str)
                        ],
                        query_params=query_params,
                        path_params=path_params,
                        request_body_schema=self._extract_request_body_schema(operation),
                        response_schema=response_schema,
                        auth_required=bool(operation.get("security") or global_security),
                        source=source,
                    )
                )

        return endpoints

    def _save_document(
        self,
        project: Project,
        document: FetchedOpenApiDocument,
    ) -> OpenApiDiscoveryResponse:
        payloads = self.parse_endpoints(document.payload, source=document.detected_format)
        created, updated, _ = EndpointService(self.db).upsert_endpoints(project.id, payloads)
        return OpenApiDiscoveryResponse(
            ok=True,
            message="OpenAPI discovery completed.",
            project_id=project.id,
            openapi_url=document.url,
            total_endpoints=len(payloads),
            created=created,
            updated=updated,
        )

    @staticmethod
    def _detect_format(payload: dict[str, Any]) -> str | None:
        if "openapi" in payload:
            return "openapi"
        if "swagger" in payload:
            return "swagger"
        return None

    @staticmethod
    def _file_extension(filename: str) -> str:
        lowered = filename.lower().strip()
        for extension in OPENAPI_FILE_EXTENSIONS:
            if lowered.endswith(extension):
                return extension
        return ""

    @staticmethod
    def _join_url(base_url: str, path: str) -> str:
        return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    @staticmethod
    def _clean_parameter(parameter: Any) -> dict[str, Any]:
        if not isinstance(parameter, dict):
            return {}
        return {
            "name": parameter.get("name"),
            "in": parameter.get("in"),
            "required": parameter.get("required", False),
            "description": parameter.get("description"),
            "schema": parameter.get("schema", {}),
        }

    def _extract_request_body_schema(self, operation: dict[str, Any]) -> dict[str, Any]:
        request_body = operation.get("requestBody")
        if isinstance(request_body, dict):
            schema = self._schema_from_content(request_body.get("content"))
            if schema:
                return schema

        # Swagger 2.0 body parameters are represented as parameters with in=body.
        for parameter in self._as_list(operation.get("parameters")):
            if isinstance(parameter, dict) and parameter.get("in") == "body":
                schema = parameter.get("schema")
                return schema if isinstance(schema, dict) else {}
        return {}

    def _extract_response_schema(self, responses: Any) -> dict[str, Any]:
        if not isinstance(responses, dict):
            return {}
        for status_code in ("200", "201", "default"):
            response = responses.get(status_code)
            if not isinstance(response, dict):
                continue
            schema = self._schema_from_content(response.get("content"))
            if schema:
                return schema
            swagger_schema = response.get("schema")
            if isinstance(swagger_schema, dict):
                return swagger_schema
        return {}

    @staticmethod
    def _schema_from_content(content: Any) -> dict[str, Any]:
        if not isinstance(content, dict):
            return {}
        preferred = content.get("application/json")
        if isinstance(preferred, dict) and isinstance(preferred.get("schema"), dict):
            return preferred["schema"]
        for media_value in content.values():
            if isinstance(media_value, dict) and isinstance(media_value.get("schema"), dict):
                return media_value["schema"]
        return {}
