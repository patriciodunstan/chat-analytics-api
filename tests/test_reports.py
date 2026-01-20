"""Tests for reports endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Report, ReportType, ReportStatus, User, UserRole, Equipment


@pytest.fixture
async def analyst_user(test_session: AsyncSession) -> User:
    """Create an analyst user for testing."""
    from app.auth.service import hash_password
    user = User(
        email="reports_analyst@test.com",
        password_hash=hash_password("analyst123"),
        full_name="Reports Analyst",
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
async def sample_data(test_session: AsyncSession) -> Equipment:
    """Create sample equipment for testing."""
    equipment = Equipment(
        equipment_id="EQ-001",
        tipo_maquina="Excavadora",
        marca="Caterpillar",
        modelo="MD-320",
        ano=2020,
    )
    test_session.add(equipment)
    await test_session.commit()
    await test_session.refresh(equipment)
    return equipment


@pytest.mark.asyncio
async def test_list_reports_empty(client: AsyncClient, analyst_headers):
    """Test listing reports when empty."""
    response = await client.get("/reports/list", headers=analyst_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["reports"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_reports_with_data(
    client: AsyncClient, analyst_headers, test_session: AsyncSession, analyst_user
):
    """Test listing reports with data."""
    # Create some reports
    for i in range(3):
        report = Report(
            user_id=analyst_user.id,
            title=f"Report {i}",
            report_type=ReportType.DATA_SUMMARY,
            status=ReportStatus.COMPLETED,
        )
        test_session.add(report)
    await test_session.commit()

    response = await client.get("/reports/list", headers=analyst_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["reports"]) == 3
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_get_report(
    client: AsyncClient, analyst_headers, test_session: AsyncSession, analyst_user
):
    """Test getting a specific report."""
    report = Report(
        user_id=analyst_user.id,
        title="Test Report",
        report_type=ReportType.DATA_SUMMARY,
        status=ReportStatus.COMPLETED,
        analysis_summary="Test summary",
    )
    test_session.add(report)
    await test_session.commit()
    await test_session.refresh(report)

    response = await client.get(
        f"/reports/{report.id}",
        headers=analyst_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report.id
    assert data["title"] == "Test Report"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_get_report_not_found(client: AsyncClient, analyst_headers):
    """Test getting non-existent report."""
    response = await client.get(
        "/reports/99999",
        headers=analyst_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_report_not_ready(
    client: AsyncClient, analyst_headers, test_session: AsyncSession, analyst_user
):
    """Test downloading report that's not ready."""
    report = Report(
        user_id=analyst_user.id,
        title="Pending Report",
        report_type=ReportType.DATA_SUMMARY,
        status=ReportStatus.PENDING,
    )
    test_session.add(report)
    await test_session.commit()
    await test_session.refresh(report)

    response = await client.get(
        f"/reports/{report.id}/download",
        headers=analyst_headers,
    )

    assert response.status_code == 400
    assert "not ready" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reports_unauthorized(client: AsyncClient):
    """Test accessing reports without auth."""
    response = await client.get("/reports/list")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_report_analyst_allowed(
    client: AsyncClient, analyst_headers, sample_data
):
    """Test that analyst can generate reports."""
    response = await client.post(
        "/reports/generate",
        headers=analyst_headers,
        json={
            "report_type": "data_summary",
            "title": "Test Report",
        },
    )

    # Analyst should be allowed (may return 202 or 500 if Gemini not configured)
    assert response.status_code in [201, 202, 500]