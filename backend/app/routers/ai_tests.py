from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.ai_test import (
    AITestAnalysisResponse,
    AITestPlanGenerateRequest,
    AITestPlanGenerateResponse,
    AITestPlanRead,
    AITestStepExecuteRequest,
    AITestStepExecuteResponse,
)
from app.services.ai_test_service import AITestService

router = APIRouter(prefix="/api/projects/{project_id}/ai-tests", tags=["ai-tests"])


def get_service(db: Session = Depends(get_db)) -> AITestService:
    return AITestService(db)


@router.post("/plans", response_model=AITestPlanGenerateResponse)
async def generate_ai_test_plan(
    project_id: int,
    payload: AITestPlanGenerateRequest,
    service: AITestService = Depends(get_service),
) -> AITestPlanGenerateResponse:
    try:
        return await service.generate_plan(project_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/plans", response_model=list[AITestPlanRead])
def list_ai_test_plans(
    project_id: int,
    service: AITestService = Depends(get_service),
) -> list[AITestPlanRead]:
    try:
        return service.list_plans(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get("/plans/{plan_id}", response_model=AITestPlanRead)
def get_ai_test_plan(
    project_id: int,
    plan_id: str,
    service: AITestService = Depends(get_service),
) -> AITestPlanRead:
    try:
        return service.get_plan(project_id, plan_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.post("/plans/{plan_id}/execute-step/{step_id}", response_model=AITestStepExecuteResponse)
async def execute_ai_test_step(
    project_id: int,
    plan_id: str,
    step_id: str,
    payload: AITestStepExecuteRequest,
    service: AITestService = Depends(get_service),
) -> AITestStepExecuteResponse:
    try:
        return await service.execute_step(project_id, plan_id, step_id, confirmed=payload.confirmed)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/plans/{plan_id}/analyze", response_model=AITestAnalysisResponse)
async def analyze_ai_test_plan(
    project_id: int,
    plan_id: str,
    service: AITestService = Depends(get_service),
) -> AITestAnalysisResponse:
    try:
        return await service.analyze_plan(project_id, plan_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
