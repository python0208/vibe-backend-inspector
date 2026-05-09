from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.report import LatestReportResponse, ReportRead, ReportSummaryRead
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/projects/{project_id}/reports", tags=["reports"])


def get_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


@router.get("/summary", response_model=ReportSummaryRead)
def get_report_summary(
    project_id: int,
    service: ReportService = Depends(get_service),
) -> ReportSummaryRead:
    try:
        return service.build_summary(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get("/latest", response_model=LatestReportResponse)
def get_latest_report(
    project_id: int,
    service: ReportService = Depends(get_service),
) -> LatestReportResponse:
    try:
        return service.latest_report(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.post("/generate", response_model=ReportRead)
def generate_report(
    project_id: int,
    service: ReportService = Depends(get_service),
) -> ReportRead:
    try:
        return service.generate_report(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get("/{report_id}", response_model=ReportRead)
def get_report(
    project_id: int,
    report_id: int,
    service: ReportService = Depends(get_service),
) -> ReportRead:
    try:
        return service.to_read_schema(service.get_report(project_id, report_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get("/{report_id}/markdown")
def get_report_markdown(
    project_id: int,
    report_id: int,
    service: ReportService = Depends(get_service),
) -> Response:
    try:
        report = service.get_report(project_id, report_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return Response(
        content=report.markdown_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="report-{report.id}.md"'},
    )
