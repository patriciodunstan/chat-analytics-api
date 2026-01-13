"""Reports service layer."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Report, ReportType, ReportStatus, User
from app.data.service import get_cost_vs_expense_data
from app.chat.llm import gemini_client
from app.reports.generator import report_generator
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


async def generate_cost_vs_expense_report(
    db: AsyncSession,
    user: User,
    request: ReportRequest,
) -> Report:
    """Generate a cost vs expense report with LLM analysis."""
    # Create report record
    report = await create_report(db, user, request)
    
    try:
        # Update status to processing
        report.status = ReportStatus.PROCESSING
        await db.commit()
        
        # Get data
        data = await get_cost_vs_expense_data(
            db, 
            request.service_id,
            request.period_start,
            request.period_end,
        )
        
        if not data:
            report.status = ReportStatus.FAILED
            report.analysis_summary = "Service not found"
            await db.commit()
            return report
        
        # Group by category
        costs_by_category = {}
        for cost in data.costs:
            costs_by_category[cost.category] = costs_by_category.get(cost.category, 0) + cost.amount
        
        expenses_by_category = {}
        for expense in data.expenses:
            expenses_by_category[expense.category] = expenses_by_category.get(expense.category, 0) + expense.amount
        
        # Generate LLM analysis
        analysis_data = {
            "service_name": data.service_name,
            "costs": [{"category": c.category, "amount": c.amount, "date": str(c.date)} for c in data.costs],
            "expenses": [{"category": e.category, "amount": e.amount, "date": str(e.date)} for e in data.expenses],
            "total_costs": data.total_costs,
            "total_expenses": data.total_expenses,
            "period": f"{request.period_start} - {request.period_end}" if request.period_start else "All time",
        }
        
        llm_result = await gemini_client.generate_analysis(
            analysis_type="cost_vs_expense",
            data=analysis_data,
        )
        
        # Generate PDF
        filepath = report_generator.generate_cost_vs_expense_report(
            service_name=data.service_name,
            total_costs=data.total_costs,
            total_expenses=data.total_expenses,
            costs_by_category=costs_by_category,
            expenses_by_category=expenses_by_category,
            analysis_text=llm_result["analysis"],
            recommendations=llm_result["recommendations"],
            period_start=request.period_start,
            period_end=request.period_end,
        )
        
        # Update report record
        report.status = ReportStatus.COMPLETED
        report.file_path = filepath
        report.analysis_summary = llm_result["analysis"][:500]  # First 500 chars
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
