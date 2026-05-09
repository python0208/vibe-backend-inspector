from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.api_endpoint import EndpointRead, OpenApiDiscoveryResponse
from app.services.endpoint_service import EndpointService
from app.services.openapi_service import OpenApiService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects/{project_id}", tags=["openapi"])


def get_project_or_404(project_id: int, db: Session) -> object:
    try:
        return ProjectService(db).get_project(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.post("/openapi/discover", response_model=OpenApiDiscoveryResponse)
async def discover_openapi(project_id: int, db: Session = Depends(get_db)) -> OpenApiDiscoveryResponse:
    project = get_project_or_404(project_id, db)
    return await OpenApiService(db).discover_from_project(project)


@router.post("/openapi/auto-detect", response_model=OpenApiDiscoveryResponse)
async def auto_detect_openapi(project_id: int, db: Session = Depends(get_db)) -> OpenApiDiscoveryResponse:
    project = get_project_or_404(project_id, db)
    return await OpenApiService(db).auto_detect_and_discover(project)


@router.get("/endpoints", response_model=list[EndpointRead])
def list_endpoints(project_id: int, db: Session = Depends(get_db)) -> list[EndpointRead]:
    get_project_or_404(project_id, db)
    service = EndpointService(db)
    return [service.to_read_schema(endpoint) for endpoint in service.list_endpoints(project_id)]


@router.get("/endpoints/{endpoint_id}", response_model=EndpointRead)
def get_endpoint(
    project_id: int,
    endpoint_id: int,
    db: Session = Depends(get_db),
) -> EndpointRead:
    get_project_or_404(project_id, db)
    service = EndpointService(db)
    try:
        endpoint = service.get_endpoint(project_id, endpoint_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return service.to_read_schema(endpoint)
