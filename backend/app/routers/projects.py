from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.project import ProjectCreate, ProjectListItem, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.get("", response_model=list[ProjectListItem])
def list_projects(service: ProjectService = Depends(get_project_service)) -> list[ProjectListItem]:
    projects = service.list_projects()
    return [
        ProjectListItem(
            id=project.id,
            name=project.name,
            project_path=project.project_path,
            service_base_url=project.service_base_url,
            openapi_url=project.openapi_url,
            database_type=project.database_type,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        for project in projects
    ]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    project = service.create_project(payload)
    return service.to_read_schema(project)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    try:
        project = service.get_project(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return service.to_read_schema(project)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    try:
        project = service.update_project(project_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return service.to_read_schema(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> Response:
    try:
        service.delete_project(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
