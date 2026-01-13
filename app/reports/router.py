"""Reports API router."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User, ReportType, ReportStatus
from app.auth.dependencies import get_current_user, require_analyst
from app.reports.schemas import ReportRequest, ReportResponse, ReportListResponse
from app.reports import service


router = APIRouter()


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    request: ReportRequest,
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Generate a new report (analyst/admin only)."""
    try:
        if request.report_type == ReportType.COST_VS_EXPENSE:
            report = await service.generate_cost_vs_expense_report(
                db, current_user, request
            )
        else:
            # For now, only cost_vs_expense is implemented
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Report type {request.report_type.value} not yet implemented",
            )
        
        return ReportResponse.model_validate(report)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}",
        )


@router.get("/list", response_model=ReportListResponse)
async def list_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 20,
) -> ReportListResponse:
    """List user's reports."""
    reports, total = await service.get_user_reports(db, current_user, skip, limit)
    
    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports],
        total=total,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Get a specific report."""
    report = await service.get_report(db, report_id, current_user)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    """Download a report PDF."""
    report = await service.get_report(db, report_id, current_user)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not ready: {report.status.value}",
        )
    
    if not report.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found",
        )
    
    return FileResponse(
        path=report.file_path,
        filename=f"{report.title}.pdf",
        media_type="application/pdf",
    )
