"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.db.models import User, UserRole
from app.auth.service import hash_password, create_user_token
from app.chat.llm import llm_client
from unittest.mock import AsyncMock


# Mock LLM client
llm_client.generate_response = AsyncMock(return_value="This is a mocked LLM response.")
llm_client.generate_analysis = AsyncMock(return_value="This is a mocked analysis.")


# Test database URL (SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_session):
    """Create a test client with database override."""
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        full_name="Test User",
        role=UserRole.ANALYST,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user) -> dict:
    """Get authentication headers for test user."""
    token = create_user_token(test_user)
    return {"Authorization": f"Bearer {token}"}
