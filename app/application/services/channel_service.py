"""Channel business logic service"""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.channel_repository import ChannelRepository
from app.domain.schemas.channel import (
    ChannelResponse, ChannelDetailResponse, ChannelListResponse,
    ChannelSubscriptionResponse, ChannelSettingsResponse,
    ChannelAdminResponse, ChannelSubscriberResponse,
    ChannelAlertResponse, ChannelStatsResponse, ChannelDeleteResponse,
    OrganizationResponse, UserBasicResponse
)


class ChannelService:
    """Service for channel business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ChannelRepository(session)

    # ============================================================
    # CRUD OPERATIONS
    # ============================================================

    async def create_channel(
        self,
        user_id: int,
        name: str,
        organization_id: int,
        description: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> ChannelResponse:
        """Create a new channel (organization admin only)"""
        # Check if user is organization admin
        from app.infrastructure.database.models import UserOrganization
        from sqlalchemy import select, and_

        org_result = await self.session.execute(
            select(UserOrganization).where(
                and_(
                    UserOrganization.user_id == user_id,
                    UserOrganization.organization_id == organization_id
                )
            )
        )
        if org_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization admins can create channels"
            )

        channel = await self.repo.create_channel(
            name=name,
            organization_id=organization_id,
            creator_id=user_id,
            description=description,
            image_url=image_url
        )

        # Creator becomes admin automatically
        await self.repo.add_channel_admin(channel.id, user_id)

        # Creator subscribes automatically
        await self.repo.subscribe_to_channel(user_id, channel.id)

        return await self._build_channel_response(channel, user_id)

    async def get_channel_by_id(self, channel_id: int, user_id: int) -> ChannelDetailResponse:
        """Get a single channel by ID"""
        channel = await self.repo.get_channel_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        return await self._build_channel_detail_response(channel, user_id)

    async def get_channels(
        self,
        user_id: int,
        organization_id: Optional[int] = None,
        subscribed_only: bool = False,
        include_hidden: bool = False,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> ChannelListResponse:
        """Get channels with filters"""
        channels, total = await self.repo.get_channels(
            user_id=user_id,
            organization_id=organization_id,
            subscribed_only=subscribed_only,
            include_hidden=include_hidden,
            search=search,
            page=page,
            page_size=page_size
        )

        # Build response for each channel
        channel_responses = []
        for channel in channels:
            channel_response = await self._build_channel_response(channel, user_id)
            channel_responses.append(channel_response)

        # Calculate pagination
        has_more = (page * page_size) < total

        return ChannelListResponse(
            channels=channel_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def update_channel(
        self,
        channel_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> ChannelResponse:
        """Update a channel (admin only)"""
        # Check if user is admin
        is_admin = await self.repo.is_user_admin(user_id, channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can update the channel"
            )

        # Update channel
        updated_channel = await self.repo.update_channel(
            channel_id=channel_id,
            name=name,
            description=description,
            image_url=image_url
        )

        if not updated_channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        return await self._build_channel_response(updated_channel, user_id)

    async def delete_channel(self, channel_id: int, user_id: int) -> ChannelDeleteResponse:
        """Delete a channel (admin only)"""
        # Check if user is admin
        is_admin = await self.repo.is_user_admin(user_id, channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can delete the channel"
            )

        # Delete channel
        success = await self.repo.delete_channel(channel_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        return ChannelDeleteResponse(
            success=True,
            message="Channel deleted successfully"
        )

    # ============================================================
    # SUBSCRIPTION OPERATIONS
    # ============================================================

    async def subscribe_to_channel(
        self,
        user_id: int,
        channel_id: int
    ) -> ChannelSubscriptionResponse:
        """Subscribe user to channel"""
        # Check channel exists
        channel = await self.repo.get_channel_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        # Subscribe
        success = await self.repo.subscribe_to_channel(user_id, channel_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already subscribed to this channel"
            )

        return ChannelSubscriptionResponse(
            success=True,
            is_subscribed=True,
            message="Successfully subscribed to channel"
        )

    async def unsubscribe_from_channel(
        self,
        user_id: int,
        channel_id: int
    ) -> ChannelSubscriptionResponse:
        """Unsubscribe user from channel"""
        success = await self.repo.unsubscribe_from_channel(user_id, channel_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are not subscribed to this channel"
            )

        return ChannelSubscriptionResponse(
            success=True,
            is_subscribed=False,
            message="Successfully unsubscribed from channel"
        )

    async def get_channel_subscribers(
        self,
        channel_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get subscribers of a channel (admin only)"""
        # Check if user is admin
        is_admin = await self.repo.is_user_admin(user_id, channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can view subscribers"
            )

        subscribers, total = await self.repo.get_channel_subscribers(
            channel_id, page, page_size
        )

        # Build response
        subscriber_responses = []
        for sub in subscribers:
            user_data = None
            if sub.user:
                user_data = UserBasicResponse(
                    id=sub.user.id,
                    username=sub.user.username,
                    nombre=sub.user.nombre,
                    apellidos=sub.user.apellidos,
                    profile_image_url=sub.user.profile_image_url
                )

            subscriber_responses.append(
                ChannelSubscriberResponse(
                    id=sub.id,
                    channel_id=sub.channel_id,
                    user_id=sub.user_id,
                    user=user_data,
                    subscribed_at=sub.created_at
                )
            )

        has_more = (page * page_size) < total

        return {
            "subscribers": subscriber_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": has_more
        }

    async def get_user_subscriptions(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> ChannelListResponse:
        """Get channels user is subscribed to"""
        channels, total = await self.repo.get_user_subscriptions(
            user_id, page, page_size
        )

        # Build response for each channel
        channel_responses = []
        for channel in channels:
            channel_response = await self._build_channel_response(channel, user_id)
            channel_responses.append(channel_response)

        has_more = (page * page_size) < total

        return ChannelListResponse(
            channels=channel_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    # ============================================================
    # ADMIN OPERATIONS
    # ============================================================

    async def add_channel_admin(
        self,
        channel_id: int,
        admin_user_id: int,
        target_user_id: int
    ) -> dict:
        """Add a channel admin (admin only)"""
        # Check if requester is admin
        is_admin = await self.repo.is_user_admin(admin_user_id, channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can add other admins"
            )

        # Add admin
        admin = await self.repo.add_channel_admin(channel_id, target_user_id)

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an admin"
            )

        return {
            "success": True,
            "message": "Admin added successfully"
        }

    async def remove_channel_admin(
        self,
        channel_id: int,
        admin_user_id: int,
        target_user_id: int
    ) -> dict:
        """Remove a channel admin (admin only)"""
        # Check if requester is admin
        is_admin = await self.repo.is_user_admin(admin_user_id, channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can remove other admins"
            )

        # Remove admin
        success = await self.repo.remove_channel_admin(channel_id, target_user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not an admin"
            )

        return {
            "success": True,
            "message": "Admin removed successfully"
        }

    async def get_channel_admins(self, channel_id: int) -> List[ChannelAdminResponse]:
        """Get all admins of a channel"""
        admins = await self.repo.get_channel_admins(channel_id)

        admin_responses = []
        for admin in admins:
            user_data = None
            if admin.user:
                user_data = UserBasicResponse(
                    id=admin.user.id,
                    username=admin.user.username,
                    nombre=admin.user.nombre,
                    apellidos=admin.user.apellidos,
                    profile_image_url=admin.user.profile_image_url
                )

            admin_responses.append(
                ChannelAdminResponse(
                    id=admin.id,
                    channel_id=admin.channel_id,
                    user_id=admin.user_id,
                    user=user_data,
                    created_at=admin.created_at
                )
            )

        return admin_responses

    # ============================================================
    # SETTINGS OPERATIONS
    # ============================================================

    async def get_channel_settings(
        self,
        user_id: int,
        channel_id: int
    ) -> ChannelSettingsResponse:
        """Get channel notification settings"""
        settings = await self.repo.get_or_create_channel_settings(user_id, channel_id)

        return ChannelSettingsResponse(
            id=settings.id,
            channel_id=settings.channel_id,
            user_id=settings.user_id,
            notifications_enabled=settings.notifications_enabled,
            post_notifications=settings.post_notifications,
            event_notifications=settings.event_notifications,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )

    async def update_channel_settings(
        self,
        user_id: int,
        channel_id: int,
        notifications_enabled: bool,
        post_notifications: bool,
        event_notifications: bool
    ) -> ChannelSettingsResponse:
        """Update channel notification settings"""
        settings = await self.repo.update_channel_settings(
            user_id=user_id,
            channel_id=channel_id,
            notifications_enabled=notifications_enabled,
            post_notifications=post_notifications,
            event_notifications=event_notifications
        )

        return ChannelSettingsResponse(
            id=settings.id,
            channel_id=settings.channel_id,
            user_id=settings.user_id,
            notifications_enabled=settings.notifications_enabled,
            post_notifications=settings.post_notifications,
            event_notifications=settings.event_notifications,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )

    # ============================================================
    # HIDE/UNHIDE OPERATIONS
    # ============================================================

    async def hide_channel(self, user_id: int, channel_id: int) -> dict:
        """Hide a channel"""
        channel = await self.repo.get_channel_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        success = await self.repo.hide_channel(user_id, channel_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Channel is already hidden"
            )

        return {"success": True, "message": "Channel hidden successfully"}

    async def unhide_channel(self, user_id: int, channel_id: int) -> dict:
        """Unhide a channel"""
        success = await self.repo.unhide_channel(user_id, channel_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Channel is not hidden"
            )

        return {"success": True, "message": "Channel unhidden successfully"}

    # ============================================================
    # ALERTS OPERATIONS
    # ============================================================

    async def create_channel_alert(
        self,
        channel_id: int,
        user_id: int,
        title: str,
        message: str
    ) -> ChannelAlertResponse:
        """Create a channel alert (admin only)"""
        # Check if user is admin
        is_admin = await self.repo.is_user_admin(user_id, channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can create alerts"
            )

        alert = await self.repo.create_channel_alert(
            channel_id=channel_id,
            title=title,
            message=message,
            created_by=user_id
        )

        return ChannelAlertResponse(
            id=alert.id,
            channel_id=alert.channel_id,
            title=alert.title,
            message=alert.message,
            created_by=alert.created_by,
            created_at=alert.created_at,
            sent_at=alert.sent_at
        )

    async def get_channel_alerts(
        self,
        channel_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get alerts for a channel"""
        alerts, total = await self.repo.get_channel_alerts(channel_id, page, page_size)

        alert_responses = [
            ChannelAlertResponse(
                id=alert.id,
                channel_id=alert.channel_id,
                title=alert.title,
                message=alert.message,
                created_by=alert.created_by,
                created_at=alert.created_at,
                sent_at=alert.sent_at
            )
            for alert in alerts
        ]

        has_more = (page * page_size) < total

        return {
            "alerts": alert_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": has_more
        }

    # ============================================================
    # STATISTICS
    # ============================================================

    async def get_channel_stats(self, channel_id: int) -> ChannelStatsResponse:
        """Get channel statistics"""
        channel = await self.repo.get_channel_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        subscribers_count = await self.repo.get_subscribers_count(channel_id)
        posts_count = await self.repo.get_posts_count(channel_id)
        events_count = await self.repo.get_events_count(channel_id)
        admins_count = await self.repo.get_admins_count(channel_id)

        return ChannelStatsResponse(
            subscribers_count=subscribers_count,
            posts_count=posts_count,
            events_count=events_count,
            admins_count=admins_count
        )

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _build_channel_response(self, channel, user_id: int) -> ChannelResponse:
        """Build basic channel response"""
        # Get counts
        subscribers_count = await self.repo.get_subscribers_count(channel.id)
        posts_count = await self.repo.get_posts_count(channel.id)
        events_count = await self.repo.get_events_count(channel.id)

        # Get user status
        is_subscribed = await self.repo.is_user_subscribed(user_id, channel.id)
        is_admin = await self.repo.is_user_admin(user_id, channel.id)
        is_hidden = await self.repo.is_channel_hidden(user_id, channel.id)

        return ChannelResponse(
            id=channel.id,
            name=channel.name,
            description=channel.description,
            organization_id=channel.organization_id,
            image_url=channel.image_url,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
            subscribers_count=subscribers_count,
            posts_count=posts_count,
            events_count=events_count,
            is_subscribed=is_subscribed,
            is_admin=is_admin,
            is_hidden=is_hidden
        )

    async def _build_channel_detail_response(
        self,
        channel,
        user_id: int
    ) -> ChannelDetailResponse:
        """Build detailed channel response with organization"""
        # Get basic response
        basic_response = await self._build_channel_response(channel, user_id)

        # Build organization response
        organization = None
        if channel.organization:
            organization = OrganizationResponse(
                id=channel.organization.id,
                name=channel.organization.name,
                image_url=channel.organization.image_url
            )

        return ChannelDetailResponse(
            **basic_response.model_dump(),
            organization=organization
        )
