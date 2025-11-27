"""Search repository - Database operations"""
from typing import Tuple, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import User, Post, Channel, Event


class SearchRepository:
    """Repository for search operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # USER SEARCH
    # ============================================================

    async def search_users(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[User], int]:
        """Search users by username, name, or surnames"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(User.id))
            .where(
                or_(
                    User.username.ilike(f"%{query}%"),
                    User.nombre.ilike(f"%{query}%"),
                    User.apellidos.ilike(f"%{query}%")
                )
            )
        )
        total = count_result.scalar() or 0

        # Get users
        result = await self.session.execute(
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
        users = result.scalars().all()

        return list(users), total

    # ============================================================
    # POST SEARCH
    # ============================================================

    async def search_posts(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Post], int]:
        """Search posts by content"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(Post.id))
            .where(Post.text_post.ilike(f"%{query}%"))
        )
        total = count_result.scalar() or 0

        # Get posts
        result = await self.session.execute(
            select(Post)
            .where(Post.text_post.ilike(f"%{query}%"))
            .order_by(Post.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        posts = result.scalars().all()

        return list(posts), total

    # ============================================================
    # CHANNEL SEARCH
    # ============================================================

    async def search_channels(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Channel], int]:
        """Search channels by name or description"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(Channel.id))
            .where(
                or_(
                    Channel.name.ilike(f"%{query}%"),
                    Channel.description.ilike(f"%{query}%")
                )
            )
        )
        total = count_result.scalar() or 0

        # Get channels
        result = await self.session.execute(
            select(Channel)
            .where(
                or_(
                    Channel.name.ilike(f"%{query}%"),
                    Channel.description.ilike(f"%{query}%")
                )
            )
            .order_by(Channel.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        channels = result.scalars().all()

        return list(channels), total

    # ============================================================
    # EVENT SEARCH
    # ============================================================

    async def search_events(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Event], int]:
        """Search events by name, description, or location"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(Event.id))
            .where(
                or_(
                    Event.name.ilike(f"%{query}%"),
                    Event.description.ilike(f"%{query}%"),
                    Event.location.ilike(f"%{query}%")
                )
            )
        )
        total = count_result.scalar() or 0

        # Get events
        result = await self.session.execute(
            select(Event)
            .where(
                or_(
                    Event.name.ilike(f"%{query}%"),
                    Event.description.ilike(f"%{query}%"),
                    Event.location.ilike(f"%{query}%")
                )
            )
            .order_by(Event.event_date)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        events = result.scalars().all()

        return list(events), total

    # ============================================================
    # GLOBAL SEARCH
    # ============================================================

    async def search_all(
        self,
        query: str,
        limit_per_type: int = 5
    ) -> dict:
        """Search across all content types"""
        # Search users
        users_result = await self.session.execute(
            select(User)
            .where(
                or_(
                    User.username.ilike(f"%{query}%"),
                    User.nombre.ilike(f"%{query}%"),
                    User.apellidos.ilike(f"%{query}%")
                )
            )
            .limit(limit_per_type)
        )
        users = list(users_result.scalars().all())

        # Search posts
        posts_result = await self.session.execute(
            select(Post)
            .where(Post.text_post.ilike(f"%{query}%"))
            .order_by(Post.created_at.desc())
            .limit(limit_per_type)
        )
        posts = list(posts_result.scalars().all())

        # Search channels
        channels_result = await self.session.execute(
            select(Channel)
            .where(
                or_(
                    Channel.name.ilike(f"%{query}%"),
                    Channel.description.ilike(f"%{query}%")
                )
            )
            .limit(limit_per_type)
        )
        channels = list(channels_result.scalars().all())

        # Search events
        events_result = await self.session.execute(
            select(Event)
            .where(
                or_(
                    Event.name.ilike(f"%{query}%"),
                    Event.description.ilike(f"%{query}%"),
                    Event.location.ilike(f"%{query}%")
                )
            )
            .limit(limit_per_type)
        )
        events = list(events_result.scalars().all())

        return {
            "users": users,
            "posts": posts,
            "channels": channels,
            "events": events
        }
