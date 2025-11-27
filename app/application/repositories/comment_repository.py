"""Comment repository for database operations"""
from typing import List, Optional, Tuple
from datetime import datetime
import secrets
from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import Comment, CommentLike, User, Post


class CommentRepository:
    """Repository for comment-related database operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _generate_id_code(self) -> str:
        """Generate unique ID code for comment"""
        return f"CMT-{secrets.token_hex(8).upper()}"

    # ============================================================
    # CRUD OPERATIONS
    # ============================================================

    async def create_comment(
        self,
        post_id: int,
        user_id: int,
        content: str
    ) -> Comment:
        """Create a new comment"""
        comment = Comment(
            id_code=self._generate_id_code(),
            post_id=post_id,
            author_id=user_id,
            text_comment=content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def get_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get comment by ID with user info"""
        result = await self.session.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_post_comments(
        self,
        post_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Comment], int]:
        """Get comments for a post"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(Comment.id))
            .where(Comment.post_id == post_id)
        )
        total = count_result.scalar() or 0

        # Get comments with user info
        query = (
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        comments = result.scalars().all()

        return list(comments), total

    async def update_comment(
        self,
        comment_id: int,
        content: str
    ) -> Optional[Comment]:
        """Update a comment"""
        comment = await self.get_comment_by_id(comment_id)
        if not comment:
            return None

        comment.text_comment = content
        comment.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int) -> bool:
        """Delete a comment"""
        comment = await self.get_comment_by_id(comment_id)
        if not comment:
            return False

        await self.session.delete(comment)
        await self.session.commit()
        return True

    # ============================================================
    # LIKE OPERATIONS
    # ============================================================

    async def add_like(self, comment_id: int, user_id: int) -> bool:
        """Add a like to a comment"""
        # Check if already liked
        existing = await self.session.execute(
            select(CommentLike).where(
                and_(
                    CommentLike.comment_id == comment_id,
                    CommentLike.user_id == user_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return False

        like = CommentLike(
            comment_id=comment_id,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        self.session.add(like)
        await self.session.commit()
        return True

    async def remove_like(self, comment_id: int, user_id: int) -> bool:
        """Remove a like from a comment"""
        result = await self.session.execute(
            delete(CommentLike).where(
                and_(
                    CommentLike.comment_id == comment_id,
                    CommentLike.user_id == user_id
                )
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def get_likes_count(self, comment_id: int) -> int:
        """Get number of likes for a comment"""
        result = await self.session.execute(
            select(func.count(CommentLike.id))
            .where(CommentLike.comment_id == comment_id)
        )
        return result.scalar() or 0

    async def is_liked_by_user(self, comment_id: int, user_id: int) -> bool:
        """Check if user liked the comment"""
        result = await self.session.execute(
            select(CommentLike).where(
                and_(
                    CommentLike.comment_id == comment_id,
                    CommentLike.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

    # ============================================================
    # STATISTICS
    # ============================================================

    async def get_post_comments_count(self, post_id: int) -> int:
        """Get number of comments for a post"""
        result = await self.session.execute(
            select(func.count(Comment.id))
            .where(Comment.post_id == post_id)
        )
        return result.scalar() or 0
