"""Reports service layer."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Report, ReportType, ReportStatus, User
from app.chat.llm import llm_client
from app.reports.schemas import ReportRequest


async def create_report(
    db: AsyncSession,
    user: User,
    request: ReportRequest,
) -> Report:
    """Create a new report record."""
    title = request.title or f"Reporte {request.report_type.value} - {datetime.now().strftime('%Y-%m-%d')}"

    report = Report(
        user_id=user.id,
        title=title,
        report_type=request.report_type,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def generate_data_summary_report(
    db: AsyncSession,
    user: User,
    request: ReportRequest,
    query_result: dict,
) -> Report:
    """Generate a data summary report with LLM analysis."""
    # Create report record
    report = await create_report(db, user, request)

    try:
        # Update status to processing
        report.status = ReportStatus.PROCESSING
        await db.commit()

        # Generate LLM analysis from query results
        llm_result = await llm_client.generate_analysis(
            analysis_type="data_summary",
            data=query_result,
        )

        # Update report record
        report.status = ReportStatus.COMPLETED
        report.analysis_summary = llm_result.get("analysis", "")[:500]
        await db.commit()
        await db.refresh(report)

        return report

    except Exception as e:
        report.status = ReportStatus.FAILED
        report.analysis_summary = f"Error: {str(e)}"
        await db.commit()
        raise


async def get_user_reports(
    db: AsyncSession,
    user: User,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Report], int]:
    """Get all reports for a user."""
    # Get total count
    count_result = await db.execute(
        select(func.count(Report.id)).where(Report.user_id == user.id)
    )
    total = count_result.scalar() or 0

    # Get reports
    result = await db.execute(
        select(Report)
        .where(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    reports = list(result.scalars().all())

    return reports, total


async def get_report(
    db: AsyncSession,
    report_id: int,
    user: User,
) -> Report | None:
    """Get a specific report by ID."""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()