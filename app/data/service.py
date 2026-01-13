"""Data service layer."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Service, Cost, Expense, User, UserRole
from app.data.schemas import ServiceCreate, CostCreate, ExpenseCreate, CostVsExpenseData


async def get_services(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[Service]:
    """Get all services."""
    result = await db.execute(
        select(Service)
        .order_by(Service.name)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_service(db: AsyncSession, service_id: int) -> Service | None:
    """Get a service by ID."""
    result = await db.execute(
        select(Service).where(Service.id == service_id)
    )
    return result.scalar_one_or_none()


async def create_service(db: AsyncSession, data: ServiceCreate) -> Service:
    """Create a new service."""
    service = Service(**data.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def get_costs_by_service(
    db: AsyncSession,
    service_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[Cost]:
    """Get costs for a service."""
    query = select(Cost).where(Cost.service_id == service_id)
    
    if start_date:
        query = query.where(Cost.date >= start_date)
    if end_date:
        query = query.where(Cost.date <= end_date)
    
    query = query.order_by(Cost.date.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_expenses_by_service(
    db: AsyncSession,
    service_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[Expense]:
    """Get expenses for a service."""
    query = select(Expense).where(Expense.service_id == service_id)
    
    if start_date:
        query = query.where(Expense.date >= start_date)
    if end_date:
        query = query.where(Expense.date <= end_date)
    
    query = query.order_by(Expense.date.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_cost(db: AsyncSession, data: CostCreate) -> Cost:
    """Create a new cost record."""
    cost = Cost(**data.model_dump())
    db.add(cost)
    await db.commit()
    await db.refresh(cost)
    return cost


async def create_expense(db: AsyncSession, data: ExpenseCreate) -> Expense:
    """Create a new expense record."""
    expense = Expense(**data.model_dump())
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def get_cost_vs_expense_data(
    db: AsyncSession,
    service_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> CostVsExpenseData | None:
    """Get combined cost vs expense data for analysis."""
    service = await get_service(db, service_id)
    if not service:
        return None
    
    costs = await get_costs_by_service(db, service_id, start_date, end_date)
    expenses = await get_expenses_by_service(db, service_id, start_date, end_date)
    
    from app.data.schemas import CostResponse, ExpenseResponse
    
    return CostVsExpenseData(
        service_id=service.id,
        service_name=service.name,
        total_costs=sum(c.amount for c in costs),
        total_expenses=sum(e.amount for e in expenses),
        costs=[CostResponse.model_validate(c) for c in costs],
        expenses=[ExpenseResponse.model_validate(e) for e in expenses],
        period_start=start_date,
        period_end=end_date,
    )


def check_data_access(user: User, resource_type: str) -> bool:
    """Check if user has access to data based on role."""
    # Viewers can only see limited data
    # Analysts and Admins can see everything
    if user.role in [UserRole.ANALYST, UserRole.ADMIN]:
        return True
    
    # Viewers have limited access
    if user.role == UserRole.VIEWER:
        return resource_type in ["services", "summary"]
    
    return False
