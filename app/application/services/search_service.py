"""Search business logic service"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.search_repository import SearchRepository
from app.domain.schemas.search import (
    UserSearchResult,
    PostSearchResult,
    ChannelSearchResult,
    EventSearchResult,
    SearchResultsResponse,
    UserSearchResponse,
    PostSearchResponse,
    ChannelSearchResponse,
    EventSearchResponse
)


class SearchService:
    """Service for search business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SearchRepository(session)

    async def search_all(
        self,
        query: str,
        limit_per_type: int = 5
    ) -> SearchResultsResponse:
        """Search across all content types"""
        results = await self.repo.search_all(query, limit_per_type)

        # Build user results
        user_results = [
            UserSearchResult(
                id=u.id,
                username=u.username,
                nombre=u.nombre,
                apellidos=u.apellidos,
                profile_image_url=u.profile_image_url,
                bio=u.bio
            )
            for u in results["users"]
        ]

        # Build post results
        post_results = [
            PostSearchResult(
                id=p.id,
                content=p.text_post,
                author_id=p.author_id,
                author_username=p.author.username if p.author else None,
                channel_id=p.channel_id,
                created_at=p.created_at
            )
            for p in results["posts"]
        ]

        # Build channel results
        channel_results = [
            ChannelSearchResult(
                id=c.id,
                name=c.name,
                description=c.description,
                image_url=c.image_url,
                organization_id=c.organization_id,
                subscribers_count=0  # Would need to count from subscriptions
            )
            for c in results["channels"]
        ]

        # Build event results
        event_results = [
            EventSearchResult(
                id=e.id,
                name=e.name,
                description=e.description,
                event_date=e.event_date,
                location=e.location,
                channel_id=e.channel_id
            )
            for e in results["events"]
        ]

        total_results = (
            len(user_results) +
            len(post_results) +
            len(channel_results) +
            len(event_results)
        )

        return SearchResultsResponse(
            users=user_results,
            posts=post_results,
            channels=channel_results,
            events=event_results,
            total_results=total_results
        )

    async def search_users(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> UserSearchResponse:
        """Search users"""
        users, total = await self.repo.search_users(query, page, page_size)

        user_results = [
            UserSearchResult(
                id=u.id,
                username=u.username,
                nombre=u.nombre,
                apellidos=u.apellidos,
                profile_image_url=u.profile_image_url,
                bio=u.bio
            )
            for u in users
        ]

        has_more = (page * page_size) < total

        return UserSearchResponse(
            users=user_results,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def search_posts(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> PostSearchResponse:
        """Search posts"""
        posts, total = await self.repo.search_posts(query, page, page_size)

        post_results = [
            PostSearchResult(
                id=p.id,
                content=p.text_post,
                author_id=p.author_id,
                author_username=p.author.username if p.author else None,
                channel_id=p.channel_id,
                created_at=p.created_at
            )
            for p in posts
        ]

        has_more = (page * page_size) < total

        return PostSearchResponse(
            posts=post_results,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def search_channels(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> ChannelSearchResponse:
        """Search channels"""
        channels, total = await self.repo.search_channels(query, page, page_size)

        channel_results = [
            ChannelSearchResult(
                id=c.id,
                name=c.name,
                description=c.description,
                image_url=c.image_url,
                organization_id=c.organization_id,
                subscribers_count=0
            )
            for c in channels
        ]

        has_more = (page * page_size) < total

        return ChannelSearchResponse(
            channels=channel_results,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def search_events(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> EventSearchResponse:
        """Search events"""
        events, total = await self.repo.search_events(query, page, page_size)

        event_results = [
            EventSearchResult(
                id=e.id,
                name=e.name,
                description=e.description,
                event_date=e.event_date,
                location=e.location,
                channel_id=e.channel_id
            )
            for e in events
        ]

        has_more = (page * page_size) < total

        return EventSearchResponse(
            events=event_results,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
