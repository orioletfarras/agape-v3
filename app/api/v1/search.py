"""Search endpoints"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.search_service import SearchService
from app.domain.schemas.search import (
    SearchResultsResponse,
    UserSearchResponse,
    PostSearchResponse,
    ChannelSearchResponse,
    EventSearchResponse
)

router = APIRouter(tags=["Search"], prefix="/search")


# Dependency
async def get_search_service(session: AsyncSession = Depends(get_db)) -> SearchService:
    return SearchService(session)


# ============================================================
# SEARCH ENDPOINTS
# ============================================================

@router.get("", response_model=SearchResultsResponse, status_code=status.HTTP_200_OK)
async def search_all(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Results per type"),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Global search across all content types

    Returns top results from:
    - Users (by username, name, surnames)
    - Posts (by content)
    - Channels (by name, description)
    - Events (by name, description, location)

    **Query Parameters:**
    - `q` (required): Search query string
    - `limit` (optional): Max results per type (default: 5, max: 20)
    """
    return await search_service.search_all(query=q, limit_per_type=limit)


@router.get("/users", response_model=UserSearchResponse, status_code=status.HTTP_200_OK)
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search users by username, name, or surnames

    Returns paginated list of users matching the query
    """
    return await search_service.search_users(
        query=q,
        page=page,
        page_size=page_size
    )


@router.get("/posts", response_model=PostSearchResponse, status_code=status.HTTP_200_OK)
async def search_posts(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search posts by content

    Returns paginated list of posts matching the query (newest first)
    """
    return await search_service.search_posts(
        query=q,
        page=page,
        page_size=page_size
    )


@router.get("/channels", response_model=ChannelSearchResponse, status_code=status.HTTP_200_OK)
async def search_channels(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search channels by name or description

    Returns paginated list of channels matching the query
    """
    return await search_service.search_channels(
        query=q,
        page=page,
        page_size=page_size
    )


@router.get("/events", response_model=EventSearchResponse, status_code=status.HTTP_200_OK)
async def search_events(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search events by name, description, or location

    Returns paginated list of events matching the query (sorted by date)
    """
    return await search_service.search_events(
        query=q,
        page=page,
        page_size=page_size
    )
