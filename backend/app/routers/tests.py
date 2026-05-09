from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.test_run import TestRequestPayload, TestRunRead
from app.services.test_service import TestService

router = APIRouter(prefix="/api/projects/{project_id}", tags=["tests"])


def get_test_service(db: Session = Depends(get_db)) -> TestService:
    return TestService(db)


@router.post("/endpoints/{endpoint_id}/test", response_model=TestRunRead)
async def run_endpoint_test(
    project_id: int,
    endpoint_id: int,
    payload: TestRequestPayload,
    service: TestService = Depends(get_test_service),
) -> TestRunRead:
    try:
        test_run = await service.run_endpoint_test(project_id, endpoint_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return service.to_read_schema(test_run)


@router.get("/test-runs", response_model=list[TestRunRead])
def list_test_runs(
    project_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    service: TestService = Depends(get_test_service),
) -> list[TestRunRead]:
    try:
        test_runs = service.list_test_runs(project_id, limit=limit)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return [service.to_read_schema(test_run) for test_run in test_runs]


@router.get("/test-runs/{test_run_id}", response_model=TestRunRead)
def get_test_run(
    project_id: int,
    test_run_id: int,
    service: TestService = Depends(get_test_service),
) -> TestRunRead:
    try:
        test_run = service.get_test_run(project_id, test_run_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return service.to_read_schema(test_run)
