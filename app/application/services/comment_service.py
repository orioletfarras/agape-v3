"""Comment business logic service"""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.comment_repository import CommentRepository
from app.application.repositories.post_repository import PostRepository
from app.domain.schemas.comment import (
    CommentResponse, CommentListResponse, CommentDeleteResponse,
    UserBasicResponse
)


class CommentService:
    """Service for comment business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CommentRepository(session)
        self.post_repo = PostRepository(session)

    async def create_comment(
        self,
        post_id: int,
        user_id: int,
        content: str
    ) -> CommentResponse:
        """Create a new comment on a post"""
        # Check if post exists
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        # Create comment
        comment = await self.repo.create_comment(post_id, user_id, content)

        return await self._build_comment_response(comment)

    async def get_post_comments(
        self,
        post_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> CommentListResponse:
        """Get comments for a post"""
        comments, total = await self.repo.get_post_comments(post_id, page, page_size)

        # Build response for each comment
        comment_responses = []
        for comment in comments:
            comment_response = await self._build_comment_response(comment)
            comment_responses.append(comment_response)

        has_more = (page * page_size) < total

        return CommentListResponse(
            comments=comment_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def update_comment(
        self,
        comment_id: int,
        user_id: int,
        content: str
    ) -> CommentResponse:
        """Update a comment (only by author)"""
        # Get comment
        comment = await self.repo.get_comment_by_id(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        # Check ownership
        if comment.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own comments"
            )

        # Update comment
        updated_comment = await self.repo.update_comment(comment_id, content)

        return await self._build_comment_response(updated_comment)

    async def delete_comment(
        self,
        comment_id: int,
        user_id: int
    ) -> CommentDeleteResponse:
        """Delete a comment (only by author)"""
        # Get comment
        comment = await self.repo.get_comment_by_id(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        # Check ownership
        if comment.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments"
            )

        # Delete comment
        success = await self.repo.delete_comment(comment_id)

        return CommentDeleteResponse(
            success=success,
            message="Comment deleted successfully" if success else "Failed to delete comment"
        )

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _build_comment_response(self, comment) -> CommentResponse:
        """Build comment response with user info"""
        user = None
        if comment.author:
            user = UserBasicResponse(
                id=comment.author.id,
                username=comment.author.username,
                nombre=comment.author.nombre,
                apellidos=comment.author.apellidos,
                profile_image_url=comment.author.profile_image_url
            )

        return CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.author_id,
            content=comment.text_comment,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            user=user
        )
