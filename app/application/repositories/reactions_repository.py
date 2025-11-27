"""Reactions repository - Database operations"""
from datetime import datetime
from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import PostLike, PostFavorite, PostPray, CommentLike


class ReactionsRepository:
    """Repository for reaction operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # POST LIKE OPERATIONS
    # ============================================================

    async def add_post_like(self, post_id: int, user_id: int) -> bool:
        """Add like to post"""
        like = PostLike(post_id=post_id, user_id=user_id, created_at=datetime.utcnow())
        self.session.add(like)
        await self.session.commit()
        return True

    async def remove_post_like(self, post_id: int, user_id: int) -> bool:
        """Remove like from post"""
        result = await self.session.execute(
            delete(PostLike).where(and_(PostLike.post_id == post_id, PostLike.user_id == user_id))
        )
        await self.session.commit()
        return result.rowcount > 0

    async def get_post_likes_count(self, post_id: int) -> int:
        """Get count of likes for post"""
        result = await self.session.execute(
            select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
        )
        return result.scalar() or 0

    async def is_post_liked_by_user(self, post_id: int, user_id: int) -> bool:
        """Check if user liked post"""
        result = await self.session.execute(
            select(PostLike).where(and_(PostLike.post_id == post_id, PostLike.user_id == user_id))
        )
        return result.scalar_one_or_none() is not None

    # ============================================================
    # POST PRAY OPERATIONS
    # ============================================================

    async def add_post_pray(self, post_id: int, user_id: int) -> bool:
        """Add pray to post"""
        pray = PostPray(post_id=post_id, user_id=user_id, created_at=datetime.utcnow())
        self.session.add(pray)
        await self.session.commit()
        return True

    async def remove_post_pray(self, post_id: int, user_id: int) -> bool:
        """Remove pray from post"""
        result = await self.session.execute(
            delete(PostPray).where(and_(PostPray.post_id == post_id, PostPray.user_id == user_id))
        )
        await self.session.commit()
        return result.rowcount > 0

    async def get_post_prays_count(self, post_id: int) -> int:
        """Get count of prays for post"""
        result = await self.session.execute(
            select(func.count(PostPray.id)).where(PostPray.post_id == post_id)
        )
        return result.scalar() or 0

    async def is_post_prayed_by_user(self, post_id: int, user_id: int) -> bool:
        """Check if user prayed for post"""
        result = await self.session.execute(
            select(PostPray).where(and_(PostPray.post_id == post_id, PostPray.user_id == user_id))
        )
        return result.scalar_one_or_none() is not None

    # ============================================================
    # POST FAVORITE OPERATIONS
    # ============================================================

    async def add_post_favorite(self, post_id: int, user_id: int) -> bool:
        """Add post to favorites"""
        favorite = PostFavorite(post_id=post_id, user_id=user_id, created_at=datetime.utcnow())
        self.session.add(favorite)
        await self.session.commit()
        return True

    async def remove_post_favorite(self, post_id: int, user_id: int) -> bool:
        """Remove post from favorites"""
        result = await self.session.execute(
            delete(PostFavorite).where(and_(PostFavorite.post_id == post_id, PostFavorite.user_id == user_id))
        )
        await self.session.commit()
        return result.rowcount > 0

    async def is_post_favorited_by_user(self, post_id: int, user_id: int) -> bool:
        """Check if user favorited post"""
        result = await self.session.execute(
            select(PostFavorite).where(and_(PostFavorite.post_id == post_id, PostFavorite.user_id == user_id))
        )
        return result.scalar_one_or_none() is not None

    # ============================================================
    # COMMENT LIKE OPERATIONS
    # ============================================================

    async def add_comment_like(self, comment_id: int, user_id: int) -> bool:
        """Add like to comment"""
        like = CommentLike(comment_id=comment_id, user_id=user_id, created_at=datetime.utcnow())
        self.session.add(like)
        await self.session.commit()
        return True

    async def remove_comment_like(self, comment_id: int, user_id: int) -> bool:
        """Remove like from comment"""
        result = await self.session.execute(
            delete(CommentLike).where(and_(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id))
        )
        await self.session.commit()
        return result.rowcount > 0

    async def get_comment_likes_count(self, comment_id: int) -> int:
        """Get count of likes for comment"""
        result = await self.session.execute(
            select(func.count(CommentLike.id)).where(CommentLike.comment_id == comment_id)
        )
        return result.scalar() or 0

    async def is_comment_liked_by_user(self, comment_id: int, user_id: int) -> bool:
        """Check if user liked comment"""
        result = await self.session.execute(
            select(CommentLike).where(and_(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id))
        )
        return result.scalar_one_or_none() is not None
