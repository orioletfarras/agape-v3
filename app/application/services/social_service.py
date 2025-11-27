"""Social service - Follow system"""
from typing import Tuple, List
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import Follow, User, Post
from app.domain.schemas.social import (
    UserBasicResponse, FollowResponse, UserListResponse, SocialStatsResponse
)


class SocialService:
    """Service for social/follow operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # FOLLOW OPERATIONS
    # ============================================================

    async def follow_user(self, follower_id: int, followed_id: int) -> FollowResponse:
        """Follow a user"""
        # Can't follow yourself
        if follower_id == followed_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot follow yourself"
            )

        # Check if already following
        existing = await self.session.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.followed_id == followed_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already following this user"
            )

        # Create follow
        follow = Follow(
            follower_id=follower_id,
            followed_id=followed_id,
            status="accepted",
            created_at=datetime.utcnow(),
            accepted_at=datetime.utcnow()
        )
        self.session.add(follow)
        await self.session.commit()

        return FollowResponse(
            success=True,
            is_following=True,
            message="Successfully followed user"
        )

    async def unfollow_user(self, follower_id: int, followed_id: int) -> FollowResponse:
        """Unfollow a user"""
        result = await self.session.execute(
            delete(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.followed_id == followed_id
                )
            )
        )
        await self.session.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are not following this user"
            )

        return FollowResponse(
            success=True,
            is_following=False,
            message="Successfully unfollowed user"
        )

    # ============================================================
    # GET FOLLOWERS/FOLLOWING
    # ============================================================

    async def get_followers(
        self,
        user_id: int,
        current_user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> UserListResponse:
        """Get user's followers"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(Follow.id))
            .where(Follow.followed_id == user_id)
        )
        total = count_result.scalar() or 0

        # Get followers
        query = (
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.followed_id == user_id)
            .order_by(Follow.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        users = result.scalars().all()

        # Build responses
        user_responses = []
        for user in users:
            user_response = await self._build_user_response(user, current_user_id)
            user_responses.append(user_response)

        has_more = (page * page_size) < total

        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def get_following(
        self,
        user_id: int,
        current_user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> UserListResponse:
        """Get users that user is following"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(Follow.id))
            .where(Follow.follower_id == user_id)
        )
        total = count_result.scalar() or 0

        # Get following
        query = (
            select(User)
            .join(Follow, Follow.followed_id == User.id)
            .where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        users = result.scalars().all()

        # Build responses
        user_responses = []
        for user in users:
            user_response = await self._build_user_response(user, current_user_id)
            user_responses.append(user_response)

        has_more = (page * page_size) < total

        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    # ============================================================
    # SEARCH & SUGGESTIONS
    # ============================================================

    async def search_users(
        self,
        query: str,
        current_user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> UserListResponse:
        """Search users by username or name"""
        # Count total
        count_query = (
            select(func.count(User.id))
            .where(
                or_(
                    User.username.ilike(f"%{query}%"),
                    User.nombre.ilike(f"%{query}%"),
                    User.apellidos.ilike(f"%{query}%")
                )
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get users
        search_query = (
            select(User)
            .where(
                or_(
                    User.username.ilike(f"%{query}%"),
                    User.nombre.ilike(f"%{query}%"),
                    User.apellidos.ilike(f"%{query}%")
                )
            )
            .order_by(User.username)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(search_query)
        users = result.scalars().all()

        # Build responses
        user_responses = []
        for user in users:
            user_response = await self._build_user_response(user, current_user_id)
            user_responses.append(user_response)

        has_more = (page * page_size) < total

        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def get_suggested_users(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[UserBasicResponse]:
        """Get suggested users to follow"""
        # Get users the current user is NOT following
        # Exclude self and already followed users
        subquery = select(Follow.followed_id).where(Follow.follower_id == user_id)

        query = (
            select(User)
            .where(
                and_(
                    User.id != user_id,
                    ~User.id.in_(subquery)
                )
            )
            .order_by(User.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        users = result.scalars().all()

        # Build responses
        user_responses = []
        for user in users:
            user_response = await self._build_user_response(user, user_id)
            user_responses.append(user_response)

        return user_responses

    # ============================================================
    # STATISTICS
    # ============================================================

    async def get_social_stats(self, user_id: int) -> SocialStatsResponse:
        """Get social statistics for a user"""
        # Followers count
        followers_result = await self.session.execute(
            select(func.count(Follow.id))
            .where(Follow.followed_id == user_id)
        )
        followers_count = followers_result.scalar() or 0

        # Following count
        following_result = await self.session.execute(
            select(func.count(Follow.id))
            .where(Follow.follower_id == user_id)
        )
        following_count = following_result.scalar() or 0

        # Posts count
        posts_result = await self.session.execute(
            select(func.count(Post.id))
            .where(Post.author_id == user_id)
        )
        posts_count = posts_result.scalar() or 0

        return SocialStatsResponse(
            user_id=user_id,
            followers_count=followers_count,
            following_count=following_count,
            posts_count=posts_count
        )

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _is_following(self, follower_id: int, followed_id: int) -> bool:
        """Check if follower is following followed"""
        result = await self.session.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.followed_id == followed_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def _get_followers_count(self, user_id: int) -> int:
        """Get followers count"""
        result = await self.session.execute(
            select(func.count(Follow.id))
            .where(Follow.followed_id == user_id)
        )
        return result.scalar() or 0

    async def _get_following_count(self, user_id: int) -> int:
        """Get following count"""
        result = await self.session.execute(
            select(func.count(Follow.id))
            .where(Follow.follower_id == user_id)
        )
        return result.scalar() or 0

    async def _build_user_response(
        self,
        user,
        current_user_id: int
    ) -> UserBasicResponse:
        """Build user response with social info"""
        followers_count = await self._get_followers_count(user.id)
        following_count = await self._get_following_count(user.id)

        # Check if current user is following this user
        is_following = await self._is_following(current_user_id, user.id)

        # Check if this user is following current user
        is_followed_by = await self._is_following(user.id, current_user_id)

        return UserBasicResponse(
            id=user.id,
            username=user.username,
            nombre=user.nombre,
            apellidos=user.apellidos,
            profile_image_url=user.profile_image_url,
            bio=user.bio,
            followers_count=followers_count,
            following_count=following_count,
            is_following=is_following,
            is_followed_by=is_followed_by
        )
