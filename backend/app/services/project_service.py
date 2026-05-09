import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.ai_test_plan import AITestPlanRecord, AITestStepRecord
from app.models.api_endpoint import ApiEndpoint
from app.models.project import Project
from app.models.test_run import TestRun
from app.schemas.project import AuthConfig, ProjectCreate, ProjectRead, ProjectUpdate
from app.utils.security import mask_secrets


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_projects(self) -> list[Project]:
        return self.db.query(Project).order_by(Project.updated_at.desc()).all()

    def get_project(self, project_id: int) -> Project:
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        return project

    def create_project(self, payload: ProjectCreate) -> Project:
        project = Project(
            name=payload.name,
            project_path=payload.project_path,
            service_base_url=payload.service_base_url,
            openapi_url=payload.openapi_url,
            database_type=payload.database_type,
            database_config_json=json.dumps(payload.database_config),
            auth_config_json=payload.auth_config.model_dump_json(),
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update_project(self, project_id: int, payload: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        update_data = payload.model_dump(exclude_unset=True)

        for field in ("name", "project_path", "service_base_url", "openapi_url", "database_type"):
            if field in update_data:
                setattr(project, field, update_data[field])

        if "database_config" in update_data:
            existing_config = self._loads(project.database_config_json)
            incoming_config = self._preserve_masked_secrets(
                existing_config,
                update_data["database_config"] or {},
            )
            project.database_config_json = json.dumps(incoming_config)

        if "auth_config" in update_data:
            auth_config = update_data["auth_config"]
            if isinstance(auth_config, AuthConfig):
                incoming_auth = auth_config.model_dump()
            else:
                incoming_auth = auth_config or {"type": "none"}
            existing_auth = self._loads(project.auth_config_json)
            project.auth_config_json = json.dumps(
                self._preserve_masked_secrets(existing_auth, incoming_auth)
            )

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int) -> None:
        project = self.get_project(project_id)
        self.db.query(AITestStepRecord).filter(AITestStepRecord.project_id == project_id).delete()
        self.db.query(AITestPlanRecord).filter(AITestPlanRecord.project_id == project_id).delete()
        self.db.query(TestRun).filter(TestRun.project_id == project_id).delete()
        self.db.query(ApiEndpoint).filter(ApiEndpoint.project_id == project_id).delete()
        self.db.delete(project)
        self.db.commit()

    def to_read_schema(self, project: Project) -> ProjectRead:
        return ProjectRead(
            id=project.id,
            name=project.name,
            project_path=project.project_path,
            service_base_url=project.service_base_url,
            openapi_url=project.openapi_url,
            database_type=project.database_type,
            database_config=mask_secrets(self._loads(project.database_config_json)),
            auth_config=AuthConfig(**mask_secrets(self._loads(project.auth_config_json))),
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @staticmethod
    def _loads(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            loaded = json.loads(raw)
            return loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            return {}

    @classmethod
    def _preserve_masked_secrets(
        cls,
        existing: dict[str, Any],
        incoming: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(incoming)
        for key, value in incoming.items():
            if isinstance(value, dict):
                merged[key] = cls._preserve_masked_secrets(
                    existing.get(key, {}) if isinstance(existing.get(key), dict) else {},
                    value,
                )
            elif value == "********" and key in existing:
                merged[key] = existing[key]
        return merged
