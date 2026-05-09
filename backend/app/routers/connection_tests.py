from fastapi import APIRouter

from app.schemas.connection import (
    DatabaseConnectionTestRequest,
    DatabaseConnectionTestResponse,
    OpenApiTestRequest,
    OpenApiTestResponse,
)
from app.services.database_service import DatabaseService
from app.services.openapi_service import OpenApiService

router = APIRouter(prefix="/api/connection-tests", tags=["connection-tests"])


@router.post("/openapi", response_model=OpenApiTestResponse)
async def test_openapi(payload: OpenApiTestRequest) -> OpenApiTestResponse:
    return await OpenApiService().test_url(payload.url)


@router.post("/database", response_model=DatabaseConnectionTestResponse)
def test_database(payload: DatabaseConnectionTestRequest) -> DatabaseConnectionTestResponse:
    ok, message = DatabaseService().test_connection(payload.database_type, payload.database_config)
    return DatabaseConnectionTestResponse(
        ok=ok,
        message=message,
        database_type=payload.database_type,
    )
