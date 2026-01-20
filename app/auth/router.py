"""Authentication API router."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.auth.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.auth.service import (
    get_user_by_email,
    create_user,
    authenticate_user,
    create_user_token,
)
from app.auth.dependencies import get_current_user
from app.db.models import User


router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password. Returns JWT token and user info.",
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Email already registered"},
    }
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Register a new user and get access token.

    **Default role**: VIEWER

    **Returns**:
    - access_token: JWT for authentication
    - user: User information (without password)
    """
    # Check if user exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = await create_user(db, user_data)
    
    # Generate token
    token = create_user_token(user)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate with email and password to get JWT token.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    }
)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Login with email and password.

    **Returns**:
    - access_token: JWT for authentication (expires in 60 minutes by default)
    - user: Current user information
    """
    user = await authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_user_token(user)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information.",
    responses={
        200: {"description": "User information retrieved"},
        401: {"description": "Not authenticated or invalid token"},
    }
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """
    Get current authenticated user information.

    **Requires**: Valid JWT token in Authorization header.

    **Returns**: User profile without sensitive data (no password).
    """
    return UserResponse.model_validate(current_user)
