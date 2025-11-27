"""FastAPI dependencies for authentication and database access"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.infrastructure.security import get_user_id_from_token


async def get_current_user(
    x_access_token: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token

    Args:
        x_access_token: JWT token from header
        session: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not x_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify and decode token
    user_id = get_user_id_from_token(x_access_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_user_optional(
    x_access_token: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Dependency to get current user (optional - doesn't raise if no token)

    Args:
        x_access_token: JWT token from header (optional)
        session: Database session

    Returns:
        User or None: Current user if authenticated, None otherwise
    """
    if not x_access_token:
        return None

    try:
        return await get_current_user(x_access_token, session)
    except HTTPException:
        return None


async def require_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to require a verified user

    Args:
        current_user: Current authenticated user

    Returns:
        User: Verified user

    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )

    return current_user


async def require_onboarding_completed(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to require onboarding to be completed

    Args:
        current_user: Current authenticated user

    Returns:
        User: User with completed onboarding

    Raises:
        HTTPException: If onboarding not completed
    """
    if not current_user.onboarding_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Onboarding must be completed first",
        )

    return current_user
