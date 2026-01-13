"""Data API router."""
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User, UserRole
from app.auth.dependencies import get_current_user, require_analyst
from app.data.schemas import (
    ServiceCreate,
    ServiceResponse,
    CostCreate,
    CostResponse,
    ExpenseCreate,
    ExpenseResponse,
    CostVsExpenseData,
)
from app.data import service


router = APIRouter()


@router.get("/services", response_model=list[ServiceResponse])
async def list_services(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> list[ServiceResponse]:
    """List all services."""
    services = await service.get_services(db, skip, limit)
    return [ServiceResponse.model_validate(s) for s in services]


@router.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: ServiceCreate,
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceResponse:
    """Create a new service (analyst/admin only)."""
    svc = await service.create_service(db, data)
    return ServiceResponse.model_validate(svc)


@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceResponse:
    """Get a service by ID."""
    svc = await service.get_service(db, service_id)
    if not svc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    return ServiceResponse.model_validate(svc)


@router.get("/services/{service_id}/costs", response_model=list[CostResponse])
async def list_service_costs(
    service_id: int,
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[CostResponse]:
    """Get costs for a service (analyst/admin only)."""
    costs = await service.get_costs_by_service(db, service_id, start_date, end_date)
    return [CostResponse.model_validate(c) for c in costs]


@router.post("/costs", response_model=CostResponse, status_code=status.HTTP_201_CREATED)
async def create_cost(
    data: CostCreate,
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CostResponse:
    """Create a new cost record (analyst/admin only)."""
    cost = await service.create_cost(db, data)
    return CostResponse.model_validate(cost)


@router.get("/services/{service_id}/expenses", response_model=list[ExpenseResponse])
async def list_service_expenses(
    service_id: int,
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[ExpenseResponse]:
    """Get expenses for a service (analyst/admin only)."""
    expenses = await service.get_expenses_by_service(db, service_id, start_date, end_date)
    return [ExpenseResponse.model_validate(e) for e in expenses]


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExpenseResponse:
    """Create a new expense record (analyst/admin only)."""
    expense = await service.create_expense(db, data)
    return ExpenseResponse.model_validate(expense)


@router.get("/analysis/cost-vs-expense/{service_id}", response_model=CostVsExpenseData)
async def get_cost_vs_expense_analysis(
    service_id: int,
    current_user: Annotated[User, Depends(require_analyst)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> CostVsExpenseData:
    """Get cost vs expense data for analysis (analyst/admin only)."""
    data = await service.get_cost_vs_expense_data(db, service_id, start_date, end_date)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    return data
