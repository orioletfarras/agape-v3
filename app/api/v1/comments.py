"""Comments endpoints"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.comment_service import CommentService
from app.domain.schemas.comment import (
    CreateCommentRequest,
    UpdateCommentRequest,
    CommentResponse,
    CommentListResponse,
    CommentDeleteResponse
)

router = APIRouter(tags=["Comments"], prefix="/comments")


# Dependency
async def get_comment_service(session: AsyncSession = Depends(get_db)) -> CommentService:
    return CommentService(session)


# ============================================================
# COMMENT CRUD ENDPOINTS
# ============================================================

@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    data: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service)
):
    """
    Create a new comment on a post

    **Requirements:**
    - Must be authenticated
    - Post must exist
    """
    return await comment_service.create_comment(
        post_id=data.post_id,
        user_id=current_user.id,
        content=data.content
    )


@router.get("/post/{post_id}", response_model=CommentListResponse, status_code=status.HTTP_200_OK)
async def get_post_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service)
):
    """
    Get comments for a post

    Returns paginated list of comments with author information
    """
    return await comment_service.get_post_comments(
        post_id=post_id,
        page=page,
        page_size=page_size
    )


@router.put("/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK)
async def update_comment(
    comment_id: int,
    data: UpdateCommentRequest,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service)
):
    """
    Update a comment

    **Requirements:**
    - Only the comment author can update it
    """
    return await comment_service.update_comment(
        comment_id=comment_id,
        user_id=current_user.id,
        content=data.content
    )


@router.delete("/{comment_id}", response_model=CommentDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service)
):
    """
    Delete a comment

    **Requirements:**
    - Only the comment author can delete it
    """
    return await comment_service.delete_comment(comment_id, current_user.id)
