"""Pydantic schemas for data module."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ServiceBase(BaseModel):
    """Base schema for Service."""
    name: str
    description: Optional[str] = None
    category: str = "general"


class ServiceCreate(ServiceBase):
    """Schema for creating a service."""
    pass


class ServiceResponse(ServiceBase):
    """Schema for service response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CostBase(BaseModel):
    """Base schema for Cost."""
    amount: float
    category: str
    description: Optional[str] = None
    date: datetime


class CostCreate(CostBase):
    """Schema for creating a cost."""
    service_id: int


class CostResponse(CostBase):
    """Schema for cost response."""
    id: int
    service_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExpenseBase(BaseModel):
    """Base schema for Expense."""
    amount: float
    category: str
    description: Optional[str] = None
    date: datetime


class ExpenseCreate(ExpenseBase):
    """Schema for creating an expense."""
    service_id: int


class ExpenseResponse(ExpenseBase):
    """Schema for expense response."""
    id: int
    service_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CostVsExpenseData(BaseModel):
    """Data for cost vs expense analysis."""
    service_id: int
    service_name: str
    total_costs: float
    total_expenses: float
    costs: list[CostResponse]
    expenses: list[ExpenseResponse]
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
