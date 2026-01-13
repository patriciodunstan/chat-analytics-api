"""Pydantic schemas for reports module."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.db.models import ReportType, ReportStatus


class ReportRequest(BaseModel):
    """Schema for requesting a new report."""
    report_type: ReportType
    service_id: int
    title: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ReportResponse(BaseModel):
    """Schema for report response."""
    id: int
    title: str
    report_type: ReportType
    status: ReportStatus
    file_path: Optional[str] = None
    analysis_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for list of reports."""
    reports: list[ReportResponse]
    total: int
