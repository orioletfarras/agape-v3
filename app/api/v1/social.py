"""Social endpoints - Follow system"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.social_service import SocialService
from app.domain.schemas.social import (
    FollowResponse,
    UserListResponse,
    UserBasicResponse,
    SocialStatsResponse
)

router = APIRouter(tags=["Social"], prefix="/social")


# Dependency
async def get_social_service(session: AsyncSession = Depends(get_db)) -> SocialService:
    return SocialService(session)


# ============================================================
# FOLLOW/UNFOLLOW ENDPOINTS
# ============================================================

@router.post("/follow/{user_id}", response_model=FollowResponse, status_code=status.HTTP_200_OK)
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(get_social_service)
):
    """
    Follow a user

    **Requirements:**
    - Must be authenticated
    - Cannot follow yourself
    - Cannot follow the same user twice
    """
    return await social_service.follow_user(
        follower_id=current_user.id,
        followed_id=user_id
    )


@router.delete("/follow/{user_id}", response_model=FollowResponse, status_code=status.HTTP_200_OK)
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(get_social_service)
):
    """
    Unfollow a user

    **Requirements:**
    - Must be authenticated
    - Must be following the user
    """
    return await social_service.unfollow_user(
        follower_id=current_user.id,
        followed_id=user_id
    )


# ============================================================
# GET FOLLOWERS/FOLLOWING ENDPOINTS
# ============================================================

@router.get("/followers/{user_id}", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def get_followers(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(get_social_service)
):
    """
    Get user's followers

    Returns paginated list of users who follow the specified user
    """
    return await social_service.get_followers(
        user_id=user_id,
        current_user_id=current_user.id,
        page=page,
        page_size=page_size
    )


@router.get("/following/{user_id}", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def get_following(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(get_social_service)
):
    """
    Get users that the specified user is following

    Returns paginated list of users
    """
    return await social_service.get_following(
        user_id=user_id,
        current_user_id=current_user.id,
        page=page,
        page_size=page_size
    )


# ============================================================
# SEARCH & SUGGESTIONS ENDPOINTS
# ============================================================

@router.get("/search", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(get_social_service)
):
    """
    Search users by username or name

    Returns paginated list of users matching the search query
    """
    return await social_service.search_users(
        query=q,
        current_user_id=current_user.id,
        page=page,
        page_size=page_size
    )


@router.get("/suggestions", response_model=list[UserBasicResponse], status_code=status.HTTP_200_OK)
async def get_suggested_users(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(get_social_service)
):
    """
    Get suggested users to follow

    Returns users that the current user is not following yet
    """
    return await social_service.get_suggested_users(
        user_id=current_user.id,
        limit=limit
    )


# ============================================================
# STATISTICS ENDPOINT
# ============================================================

@router.get("/stats/{user_id}", response_model=SocialStatsResponse, status_code=status.HTTP_200_OK)
async def get_social_stats(
    user_id: int,
    current_user: User = Depends(get_current_user),
    social_service: SocialService = Depends(get_social_service)
):
    """
    Get social statistics for a user

    Returns follower count, following count, and posts count
    """
    return await social_service.get_social_stats(user_id)
