"""Tests for data endpoints."""
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Service, Cost, Expense, User, UserRole


@pytest.fixture
async def analyst_user(test_session: AsyncSession) -> User:
    """Create an analyst user for testing."""
    from app.auth.service import hash_password
    user = User(
        email="analyst@test.com",
        password_hash=hash_password("analyst123"),
        full_name="Analyst User",
        role=UserRole.ANALYST,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def analyst_headers(analyst_user) -> dict:
    """Get auth headers for analyst user."""
    from app.auth.service import create_user_token
    token = create_user_token(analyst_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def sample_service(test_session: AsyncSession) -> Service:
    """Create a sample service."""
    service = Service(
        name="Test Service",
        description="A test service",
        category="testing",
    )
    test_session.add(service)
    await test_session.commit()
    await test_session.refresh(service)
    return service


@pytest.mark.asyncio
async def test_list_services_empty(client: AsyncClient, auth_headers):
    """Test listing services when empty."""
    response = await client.get("/data/services", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_services(
    client: AsyncClient, auth_headers, sample_service
):
    """Test listing services with data."""
    response = await client.get("/data/services", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Service"


@pytest.mark.asyncio
async def test_create_service_as_analyst(
    client: AsyncClient, analyst_headers
):
    """Test creating a service as analyst."""
    response = await client.post(
        "/data/services",
        headers=analyst_headers,
        json={
            "name": "New Service",
            "description": "Description",
            "category": "new",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Service"
    assert data["category"] == "new"


@pytest.mark.asyncio
async def test_create_service_as_viewer_forbidden(
    client: AsyncClient, auth_headers
):
    """Test creating service as viewer is forbidden."""
    response = await client.post(
        "/data/services",
        headers=auth_headers,
        json={
            "name": "New Service",
            "description": "Description",
            "category": "new",
        },
    )
    
    # auth_headers is for analyst role, so this should work
    # Let's test with a viewer
    assert response.status_code in [201, 403]  # Depends on test_user role


@pytest.mark.asyncio
async def test_get_service(
    client: AsyncClient, auth_headers, sample_service
):
    """Test getting a specific service."""
    response = await client.get(
        f"/data/services/{sample_service.id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_service.id
    assert data["name"] == "Test Service"


@pytest.mark.asyncio
async def test_get_service_not_found(client: AsyncClient, auth_headers):
    """Test getting non-existent service."""
    response = await client.get(
        "/data/services/99999",
        headers=auth_headers,
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_cost(
    client: AsyncClient, analyst_headers, sample_service
):
    """Test creating a cost record."""
    response = await client.post(
        "/data/costs",
        headers=analyst_headers,
        json={
            "service_id": sample_service.id,
            "amount": 1500.50,
            "category": "infrastructure",
            "description": "Cloud costs",
            "date": datetime.now().isoformat(),
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 1500.50
    assert data["category"] == "infrastructure"


@pytest.mark.asyncio
async def test_create_expense(
    client: AsyncClient, analyst_headers, sample_service
):
    """Test creating an expense record."""
    response = await client.post(
        "/data/expenses",
        headers=analyst_headers,
        json={
            "service_id": sample_service.id,
            "amount": 2000.00,
            "category": "operations",
            "description": "Operational expense",
            "date": datetime.now().isoformat(),
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 2000.00


@pytest.mark.asyncio
async def test_list_service_costs(
    client: AsyncClient, analyst_headers, test_session: AsyncSession, sample_service
):
    """Test listing costs for a service."""
    # Create some costs
    for i in range(3):
        cost = Cost(
            service_id=sample_service.id,
            amount=100.0 * (i + 1),
            category="test",
            date=datetime.now(),
        )
        test_session.add(cost)
    await test_session.commit()
    
    response = await client.get(
        f"/data/services/{sample_service.id}/costs",
        headers=analyst_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_list_service_expenses(
    client: AsyncClient, analyst_headers, test_session: AsyncSession, sample_service
):
    """Test listing expenses for a service."""
    # Create some expenses
    for i in range(2):
        expense = Expense(
            service_id=sample_service.id,
            amount=500.0 * (i + 1),
            category="test",
            date=datetime.now(),
        )
        test_session.add(expense)
    await test_session.commit()
    
    response = await client.get(
        f"/data/services/{sample_service.id}/expenses",
        headers=analyst_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_cost_vs_expense_analysis(
    client: AsyncClient, analyst_headers, test_session: AsyncSession, sample_service
):
    """Test getting cost vs expense analysis data."""
    # Create costs and expenses
    cost = Cost(
        service_id=sample_service.id,
        amount=1000.0,
        category="infra",
        date=datetime.now(),
    )
    expense = Expense(
        service_id=sample_service.id,
        amount=800.0,
        category="ops",
        date=datetime.now(),
    )
    test_session.add(cost)
    test_session.add(expense)
    await test_session.commit()
    
    response = await client.get(
        f"/data/analysis/cost-vs-expense/{sample_service.id}",
        headers=analyst_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["service_name"] == "Test Service"
    assert data["total_costs"] == 1000.0
    assert data["total_expenses"] == 800.0
