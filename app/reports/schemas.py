"""Pydantic schemas for reports module."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.db.models import ReportType, ReportStatus


class ReportRequest(BaseModel):
    """Schema for requesting a new report."""
    report_type: ReportType
    title: Optional[str] = None


class ReportResponse(BaseModel):
    """Schema for report response."""
    id: int
    title: str
    report_type: ReportType
    status: ReportStatus
    file_path: Optional[str] = None
    analysis_summary: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReportListResponse(BaseModel):
    """Schema for list of reports."""
    reports: list[ReportResponse]
    total: int