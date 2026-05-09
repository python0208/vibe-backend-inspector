from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.project import Project
from app.schemas.db_schema import DatabaseInspectResponse, DatabaseProjectConnectionTestResponse
from app.services.database_service import DatabaseService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects/{project_id}/database", tags=["database"])


def get_project_or_404(project_id: int, db: Session) -> Project:
    try:
        return ProjectService(db).get_project(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.post("/test-connection", response_model=DatabaseProjectConnectionTestResponse)
def test_project_database_connection(
    project_id: int,
    db: Session = Depends(get_db),
) -> DatabaseProjectConnectionTestResponse:
    project = get_project_or_404(project_id, db)
    return DatabaseService().test_project_connection(project)


@router.post("/inspect", response_model=DatabaseInspectResponse)
def inspect_project_database(
    project_id: int,
    db: Session = Depends(get_db),
) -> DatabaseInspectResponse:
    project = get_project_or_404(project_id, db)
    return DatabaseService().inspect_project_database(project)


@router.get("/schema", response_model=DatabaseInspectResponse)
def get_project_database_schema(
    project_id: int,
    db: Session = Depends(get_db),
) -> DatabaseInspectResponse:
    project = get_project_or_404(project_id, db)
    return DatabaseService().inspect_project_database(project)
