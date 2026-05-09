from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigRead,
    LLMConfigTestResponse,
    LLMConfigUpdate,
)
from app.services.llm_config_service import LLMConfigService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/llm/configs", tags=["llm"])


def get_service(db: Session = Depends(get_db)) -> LLMConfigService:
    return LLMConfigService(db)


@router.get("", response_model=list[LLMConfigRead])
def list_llm_configs(service: LLMConfigService = Depends(get_service)) -> list[LLMConfigRead]:
    return [service.to_read_schema(config) for config in service.list_configs()]


@router.post("", response_model=LLMConfigRead, status_code=status.HTTP_201_CREATED)
def create_llm_config(
    payload: LLMConfigCreate,
    service: LLMConfigService = Depends(get_service),
) -> LLMConfigRead:
    return service.to_read_schema(service.create_config(payload))


@router.put("/{config_id}", response_model=LLMConfigRead)
def update_llm_config(
    config_id: int,
    payload: LLMConfigUpdate,
    service: LLMConfigService = Depends(get_service),
) -> LLMConfigRead:
    try:
        config = service.update_config(config_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return service.to_read_schema(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_llm_config(
    config_id: int,
    service: LLMConfigService = Depends(get_service),
) -> Response:
    try:
        service.delete_config(config_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{config_id}/test", response_model=LLMConfigTestResponse)
async def test_llm_config(
    config_id: int,
    service: LLMConfigService = Depends(get_service),
) -> LLMConfigTestResponse:
    try:
        config = service.get_config(config_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    ok, message = await LLMService().test_connection(config)
    return LLMConfigTestResponse(
        ok=ok,
        message=message,
        provider=config.provider,
        model_name=config.model_name,
    )
