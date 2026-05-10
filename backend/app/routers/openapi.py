from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.api_endpoint import (
    EndpointCreate,
    EndpointDeleteResponse,
    EndpointRead,
    EndpointUpdate,
    OpenApiDiscoveryResponse,
)
from app.services.endpoint_service import EndpointConflictError, EndpointService, EndpointValidationError
from app.services.openapi_service import MAX_OPENAPI_FILE_BYTES, OpenApiFileImportError, OpenApiService
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


@router.post("/openapi/import-file", response_model=OpenApiDiscoveryResponse)
async def import_openapi_file(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> OpenApiDiscoveryResponse:
    project = get_project_or_404(project_id, db)
    content = await file.read(MAX_OPENAPI_FILE_BYTES + 1)
    try:
        return OpenApiService(db).import_document_file(project, file.filename or "", content)
    except OpenApiFileImportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except EndpointValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


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


@router.post("/endpoints", response_model=EndpointRead, status_code=status.HTTP_201_CREATED)
def create_endpoint(
    project_id: int,
    payload: EndpointCreate,
    db: Session = Depends(get_db),
) -> EndpointRead:
    get_project_or_404(project_id, db)
    service = EndpointService(db)
    try:
        endpoint = service.create_manual_endpoint(project_id, payload)
    except EndpointConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EndpointValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return service.to_read_schema(endpoint)


@router.put("/endpoints/{endpoint_id}", response_model=EndpointRead)
def update_endpoint(
    project_id: int,
    endpoint_id: int,
    payload: EndpointUpdate,
    db: Session = Depends(get_db),
) -> EndpointRead:
    get_project_or_404(project_id, db)
    service = EndpointService(db)
    try:
        endpoint = service.update_manual_endpoint(project_id, endpoint_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except EndpointConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EndpointValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return service.to_read_schema(endpoint)


@router.delete("/endpoints/{endpoint_id}", response_model=EndpointDeleteResponse)
def delete_endpoint(
    project_id: int,
    endpoint_id: int,
    db: Session = Depends(get_db),
) -> EndpointDeleteResponse:
    get_project_or_404(project_id, db)
    service = EndpointService(db)
    try:
        service.delete_manual_endpoint(project_id, endpoint_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except EndpointValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EndpointDeleteResponse(ok=True, message="Endpoint deleted.")
