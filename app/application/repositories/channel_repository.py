"""Channel repository for database operations"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    Channel, ChannelSubscription, ChannelAdmin, ChannelSetting,
    HiddenChannel, ChannelAlert, Organization, User, Post, Event
)
from app.infrastructure.security import generate_id_code


class ChannelRepository:
    """Repository for channel-related database operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # CRUD OPERATIONS
    # ============================================================

    async def create_channel(
        self,
        name: str,
        organization_id: int,
        creator_id: int,
        description: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Channel:
        """Create a new channel"""
        channel = Channel(
            id_code=generate_id_code("CH"),
            name=name,
            description=description,
            organization_id=organization_id,
            creator_id=creator_id,
            image_url=image_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def get_channel_by_id(self, channel_id: int) -> Optional[Channel]:
        """Get channel by ID with related data"""
        result = await self.session.execute(
            select(Channel)
            .options(selectinload(Channel.organization))
            .where(Channel.id == channel_id)
        )
        return result.scalar_one_or_none()

    async def get_channels(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        subscribed_only: bool = False,
        include_hidden: bool = False,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Channel], int]:
        """
        Get channels with filters
        Returns (channels, total_count)
        """
        query = select(Channel).options(selectinload(Channel.organization))

        # Filter by organization
        if organization_id:
            query = query.where(Channel.organization_id == organization_id)

        # Filter subscribed channels only
        if subscribed_only and user_id:
            query = query.join(
                ChannelSubscription,
                ChannelSubscription.channel_id == Channel.id
            ).where(ChannelSubscription.user_id == user_id)

        # Filter hidden channels
        if not include_hidden and user_id:
            hidden_subquery = (
                select(HiddenChannel.channel_id)
                .where(HiddenChannel.user_id == user_id)
            )
            query = query.where(~Channel.id.in_(hidden_subquery))

        # Search by name or description
        if search:
            query = query.where(
                or_(
                    Channel.name.ilike(f"%{search}%"),
                    Channel.description.ilike(f"%{search}%")
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Channel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.session.execute(query)
        channels = result.scalars().all()

        return list(channels), total

    async def update_channel(
        self,
        channel_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Optional[Channel]:
        """Update a channel"""
        channel = await self.get_channel_by_id(channel_id)
        if not channel:
            return None

        if name is not None:
            channel.name = name
        if description is not None:
            channel.description = description
        if image_url is not None:
            channel.image_url = image_url

        channel.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def delete_channel(self, channel_id: int) -> bool:
        """Delete a channel"""
        channel = await self.get_channel_by_id(channel_id)
        if not channel:
            return False

        await self.session.delete(channel)
        await self.session.commit()
        return True

    # ============================================================
    # SUBSCRIPTION OPERATIONS
    # ============================================================

    async def subscribe_to_channel(self, user_id: int, channel_id: int) -> bool:
        """Subscribe user to channel"""
        # Check if already subscribed
        existing = await self.session.execute(
            select(ChannelSubscription).where(
                and_(
                    ChannelSubscription.user_id == user_id,
                    ChannelSubscription.channel_id == channel_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return False

        subscription = ChannelSubscription(
            user_id=user_id,
            channel_id=channel_id
        )
        self.session.add(subscription)
        await self.session.commit()
        return True

    async def unsubscribe_from_channel(self, user_id: int, channel_id: int) -> bool:
        """Unsubscribe user from channel"""
        result = await self.session.execute(
            delete(ChannelSubscription).where(
                and_(
                    ChannelSubscription.user_id == user_id,
                    ChannelSubscription.channel_id == channel_id
                )
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def is_user_subscribed(self, user_id: int, channel_id: int) -> bool:
        """Check if user is subscribed to channel"""
        result = await self.session.execute(
            select(ChannelSubscription).where(
                and_(
                    ChannelSubscription.user_id == user_id,
                    ChannelSubscription.channel_id == channel_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_channel_subscribers(
        self,
        channel_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ChannelSubscription], int]:
        """Get subscribers of a channel"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(ChannelSubscription.id))
            .where(ChannelSubscription.channel_id == channel_id)
        )
        total = count_result.scalar() or 0

        # Get subscribers with user info
        query = (
            select(ChannelSubscription)
            .options(selectinload(ChannelSubscription.user))
            .where(ChannelSubscription.channel_id == channel_id)
            .order_by(ChannelSubscription.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        subscribers = result.scalars().all()

        return list(subscribers), total

    async def get_user_subscriptions(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Channel], int]:
        """Get channels user is subscribed to"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(ChannelSubscription.id))
            .where(ChannelSubscription.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # Get channels
        query = (
            select(Channel)
            .join(ChannelSubscription, ChannelSubscription.channel_id == Channel.id)
            .options(selectinload(Channel.organization))
            .where(ChannelSubscription.user_id == user_id)
            .order_by(ChannelSubscription.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        channels = result.scalars().all()

        return list(channels), total

    # ============================================================
    # ADMIN OPERATIONS
    # ============================================================

    async def add_channel_admin(self, channel_id: int, user_id: int) -> ChannelAdmin:
        """Add a channel admin"""
        # Check if already admin
        existing = await self.session.execute(
            select(ChannelAdmin).where(
                and_(
                    ChannelAdmin.channel_id == channel_id,
                    ChannelAdmin.user_id == user_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return None

        admin = ChannelAdmin(
            channel_id=channel_id,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        self.session.add(admin)
        await self.session.commit()
        await self.session.refresh(admin)
        return admin

    async def remove_channel_admin(self, channel_id: int, user_id: int) -> bool:
        """Remove a channel admin"""
        result = await self.session.execute(
            delete(ChannelAdmin).where(
                and_(
                    ChannelAdmin.channel_id == channel_id,
                    ChannelAdmin.user_id == user_id
                )
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def is_user_admin(self, user_id: int, channel_id: int) -> bool:
        """
        Check if user is admin of channel.
        User is admin if:
        - Is in channel_admins table, OR
        - Is channel creator, OR
        - Is organization admin (member of channel's organization via UserOrganization)
        """
        from app.infrastructure.database.models import UserOrganization

        # Get channel
        channel_result = await self.session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        if not channel:
            return False

        # Check if user is channel creator
        if channel.creator_id == user_id:
            return True

        # Check if user is channel admin
        admin_result = await self.session.execute(
            select(ChannelAdmin).where(
                and_(
                    ChannelAdmin.user_id == user_id,
                    ChannelAdmin.channel_id == channel_id
                )
            )
        )
        if admin_result.scalar_one_or_none() is not None:
            return True

        # Check if user is organization admin (if channel has organization)
        if channel.organization_id:
            org_result = await self.session.execute(
                select(UserOrganization).where(
                    and_(
                        UserOrganization.user_id == user_id,
                        UserOrganization.organization_id == channel.organization_id
                    )
                )
            )
            if org_result.scalar_one_or_none() is not None:
                return True

        return False

    async def get_channel_admins(self, channel_id: int) -> List[ChannelAdmin]:
        """Get all admins of a channel"""
        result = await self.session.execute(
            select(ChannelAdmin)
            .options(selectinload(ChannelAdmin.user))
            .where(ChannelAdmin.channel_id == channel_id)
            .order_by(ChannelAdmin.created_at.asc())
        )
        return list(result.scalars().all())

    # ============================================================
    # SETTINGS OPERATIONS
    # ============================================================

    async def get_or_create_channel_settings(
        self,
        user_id: int,
        channel_id: int
    ) -> ChannelSetting:
        """Get or create channel notification settings"""
        result = await self.session.execute(
            select(ChannelSetting).where(
                and_(
                    ChannelSetting.user_id == user_id,
                    ChannelSetting.channel_id == channel_id
                )
            )
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = ChannelSetting(
                user_id=user_id,
                channel_id=channel_id,
                notifications_enabled=True,
                post_notifications=True,
                event_notifications=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)

        return settings

    async def update_channel_settings(
        self,
        user_id: int,
        channel_id: int,
        notifications_enabled: Optional[bool] = None,
        post_notifications: Optional[bool] = None,
        event_notifications: Optional[bool] = None
    ) -> ChannelSetting:
        """Update channel notification settings"""
        settings = await self.get_or_create_channel_settings(user_id, channel_id)

        if notifications_enabled is not None:
            settings.notifications_enabled = notifications_enabled
        if post_notifications is not None:
            settings.post_notifications = post_notifications
        if event_notifications is not None:
            settings.event_notifications = event_notifications

        settings.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    # ============================================================
    # HIDE/UNHIDE OPERATIONS
    # ============================================================

    async def hide_channel(self, user_id: int, channel_id: int) -> bool:
        """Hide a channel for user"""
        existing = await self.session.execute(
            select(HiddenChannel).where(
                and_(
                    HiddenChannel.user_id == user_id,
                    HiddenChannel.channel_id == channel_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return False

        hidden = HiddenChannel(
            user_id=user_id,
            channel_id=channel_id,
            created_at=datetime.utcnow()
        )
        self.session.add(hidden)
        await self.session.commit()
        return True

    async def unhide_channel(self, user_id: int, channel_id: int) -> bool:
        """Unhide a channel for user"""
        result = await self.session.execute(
            delete(HiddenChannel).where(
                and_(
                    HiddenChannel.user_id == user_id,
                    HiddenChannel.channel_id == channel_id
                )
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def is_channel_hidden(self, user_id: int, channel_id: int) -> bool:
        """Check if channel is hidden by user"""
        result = await self.session.execute(
            select(HiddenChannel).where(
                and_(
                    HiddenChannel.user_id == user_id,
                    HiddenChannel.channel_id == channel_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

    # ============================================================
    # ALERTS OPERATIONS
    # ============================================================

    async def create_channel_alert(
        self,
        channel_id: int,
        title: str,
        message: str,
        created_by: int
    ) -> ChannelAlert:
        """Create a channel alert"""
        alert = ChannelAlert(
            channel_id=channel_id,
            title=title,
            message=message,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_channel_alerts(
        self,
        channel_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ChannelAlert], int]:
        """Get alerts for a channel"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(ChannelAlert.id))
            .where(ChannelAlert.channel_id == channel_id)
        )
        total = count_result.scalar() or 0

        # Get alerts
        query = (
            select(ChannelAlert)
            .where(ChannelAlert.channel_id == channel_id)
            .order_by(ChannelAlert.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        alerts = result.scalars().all()

        return list(alerts), total

    # ============================================================
    # STATISTICS
    # ============================================================

    async def get_subscribers_count(self, channel_id: int) -> int:
        """Get number of subscribers"""
        result = await self.session.execute(
            select(func.count(ChannelSubscription.id))
            .where(ChannelSubscription.channel_id == channel_id)
        )
        return result.scalar() or 0

    async def get_posts_count(self, channel_id: int) -> int:
        """Get number of posts in channel"""
        result = await self.session.execute(
            select(func.count(Post.id))
            .where(Post.channel_id == channel_id)
        )
        return result.scalar() or 0

    async def get_events_count(self, channel_id: int) -> int:
        """Get number of events in channel"""
        result = await self.session.execute(
            select(func.count(Event.id))
            .where(Event.channel_id == channel_id)
        )
        return result.scalar() or 0

    async def get_admins_count(self, channel_id: int) -> int:
        """Get number of admins"""
        result = await self.session.execute(
            select(func.count(ChannelAdmin.id))
            .where(ChannelAdmin.channel_id == channel_id)
        )
        return result.scalar() or 0
