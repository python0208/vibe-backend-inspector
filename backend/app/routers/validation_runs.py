from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.validation_run import (
    ValidationRunCancelResponse,
    ValidationRunCreate,
    ValidationRunDetailRead,
    ValidationRunItemRead,
    ValidationRunRead,
)
from app.services.validation_service import ValidationService

router = APIRouter(prefix="/api/projects/{project_id}/validation-runs", tags=["validation-runs"])


def get_service(db: Session = Depends(get_db)) -> ValidationService:
    return ValidationService(db)


@router.post("", response_model=ValidationRunDetailRead, status_code=status.HTTP_201_CREATED)
async def create_validation_run(
    project_id: int,
    payload: ValidationRunCreate,
    service: ValidationService = Depends(get_service),
) -> ValidationRunDetailRead:
    try:
        run = await service.create_and_run(project_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return service.to_detail_schema(run)


@router.get("", response_model=list[ValidationRunRead])
def list_validation_runs(
    project_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    service: ValidationService = Depends(get_service),
) -> list[ValidationRunRead]:
    try:
        runs = service.list_runs(project_id, limit=limit)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return [service.to_read_schema(run) for run in runs]


@router.get("/{run_id}", response_model=ValidationRunDetailRead)
def get_validation_run(
    project_id: int,
    run_id: int,
    service: ValidationService = Depends(get_service),
) -> ValidationRunDetailRead:
    try:
        run = service.get_run(project_id, run_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return service.to_detail_schema(run)


@router.get("/{run_id}/items", response_model=list[ValidationRunItemRead])
def list_validation_run_items(
    project_id: int,
    run_id: int,
    service: ValidationService = Depends(get_service),
) -> list[ValidationRunItemRead]:
    try:
        items = service.list_items(project_id, run_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return [service.to_item_schema(item) for item in items]


@router.post("/{run_id}/cancel", response_model=ValidationRunCancelResponse)
def cancel_validation_run(
    project_id: int,
    run_id: int,
    service: ValidationService = Depends(get_service),
) -> ValidationRunCancelResponse:
    try:
        return service.cancel_run(project_id, run_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
