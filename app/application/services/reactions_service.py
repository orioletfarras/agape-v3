"""Reactions business logic service"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.reactions_repository import ReactionsRepository
from app.domain.schemas.reactions import ReactionResponse


class ReactionsService:
    """Service for reactions business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ReactionsRepository(session)

    async def toggle_post_like(self, post_id: int, user_id: int, action: str) -> ReactionResponse:
        """Toggle like on post"""
        if action == "like":
            # Check if already liked
            is_liked = await self.repo.is_post_liked_by_user(post_id, user_id)
            if not is_liked:
                await self.repo.add_post_like(post_id, user_id)

            count = await self.repo.get_post_likes_count(post_id)
            return ReactionResponse(
                success=True,
                is_reacted=True,
                message="Post liked",
                reaction_count=count
            )
        else:  # unlike
            await self.repo.remove_post_like(post_id, user_id)
            count = await self.repo.get_post_likes_count(post_id)
            return ReactionResponse(
                success=True,
                is_reacted=False,
                message="Post unliked",
                reaction_count=count
            )

    async def toggle_post_pray(self, post_id: int, user_id: int, action: str) -> ReactionResponse:
        """Toggle pray on post"""
        if action == "pray":
            is_prayed = await self.repo.is_post_prayed_by_user(post_id, user_id)
            if not is_prayed:
                await self.repo.add_post_pray(post_id, user_id)

            count = await self.repo.get_post_prays_count(post_id)
            return ReactionResponse(
                success=True,
                is_reacted=True,
                message="Post prayed",
                reaction_count=count
            )
        else:  # unpray
            await self.repo.remove_post_pray(post_id, user_id)
            count = await self.repo.get_post_prays_count(post_id)
            return ReactionResponse(
                success=True,
                is_reacted=False,
                message="Post unprayed",
                reaction_count=count
            )

    async def toggle_post_favorite(self, post_id: int, user_id: int, action: str) -> ReactionResponse:
        """Toggle favorite on post"""
        if action == "favorite":
            is_favorited = await self.repo.is_post_favorited_by_user(post_id, user_id)
            if not is_favorited:
                await self.repo.add_post_favorite(post_id, user_id)

            return ReactionResponse(
                success=True,
                is_reacted=True,
                message="Post added to favorites",
                reaction_count=0
            )
        else:  # unfavorite
            await self.repo.remove_post_favorite(post_id, user_id)
            return ReactionResponse(
                success=True,
                is_reacted=False,
                message="Post removed from favorites",
                reaction_count=0
            )

    async def toggle_comment_like(self, comment_id: int, user_id: int, action: str) -> ReactionResponse:
        """Toggle like on comment"""
        if action == "like":
            is_liked = await self.repo.is_comment_liked_by_user(comment_id, user_id)
            if not is_liked:
                await self.repo.add_comment_like(comment_id, user_id)

            count = await self.repo.get_comment_likes_count(comment_id)
            return ReactionResponse(
                success=True,
                is_reacted=True,
                message="Comment liked",
                reaction_count=count
            )
        else:  # unlike
            await self.repo.remove_comment_like(comment_id, user_id)
            count = await self.repo.get_comment_likes_count(comment_id)
            return ReactionResponse(
                success=True,
                is_reacted=False,
                message="Comment unliked",
                reaction_count=count
            )
