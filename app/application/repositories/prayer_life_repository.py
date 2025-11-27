"""Prayer Life repository - Database operations"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from sqlalchemy import select, and_, or_, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import secrets

from app.infrastructure.database.models import (
    Channel,
    ChannelSubscription,
    HiddenChannel,
    AutomaticChannelContent,
    UserChannelOrder,
    PrayerLifeWebAccess,
    User
)


class PrayerLifeRepository:
    """Repository for prayer life and automatic channels"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_automatic_channels_by_language(
        self,
        language: str,
        user_id: Optional[int] = None
    ) -> List[Channel]:
        """Get all automatic channels filtered by language"""
        query = select(Channel).where(
            and_(
                Channel.is_automatic == True,
                Channel.language == language
            )
        ).order_by(Channel.category, Channel.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

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

    async def get_channel_content(
        self,
        channel_id: int,
        date: Optional[datetime] = None
    ) -> Optional[AutomaticChannelContent]:
        """Get content for a channel (optionally for specific date)"""
        query = select(AutomaticChannelContent).where(
            AutomaticChannelContent.channel_id == channel_id
        )

        if date:
            # Get content for specific date
            query = query.where(
                func.date(AutomaticChannelContent.date) == date.date()
            )
        else:
            # Get most recent content
            query = query.order_by(AutomaticChannelContent.date.desc())

        query = query.limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_channel_by_id_code(self, id_code: str) -> Optional[Channel]:
        """Get channel by id_code"""
        result = await self.session.execute(
            select(Channel).where(Channel.id_code == id_code)
        )
        return result.scalar_one_or_none()

    async def subscribe_to_channel(self, user_id: int, channel_id: int) -> bool:
        """Subscribe user to channel"""
        # Check if already subscribed
        existing = await self.is_user_subscribed(user_id, channel_id)
        if existing:
            return False

        subscription = ChannelSubscription(
            user_id=user_id,
            channel_id=channel_id,
            created_at=datetime.utcnow()
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

    async def save_channel_order(
        self,
        user_id: int,
        channel_id_codes: List[str]
    ) -> bool:
        """Save user's custom channel order"""
        # Delete existing orders
        await self.session.execute(
            delete(UserChannelOrder).where(UserChannelOrder.user_id == user_id)
        )

        # Insert new orders
        for idx, id_code in enumerate(channel_id_codes):
            order = UserChannelOrder(
                user_id=user_id,
                channel_id_code=id_code,
                order_position=idx,
                created_at=datetime.utcnow()
            )
            self.session.add(order)

        await self.session.commit()
        return True

    async def get_user_channel_order(self, user_id: int) -> List[str]:
        """Get user's custom channel order"""
        result = await self.session.execute(
            select(UserChannelOrder.channel_id_code)
            .where(UserChannelOrder.user_id == user_id)
            .order_by(UserChannelOrder.order_position)
        )
        return list(result.scalars().all())

    async def toggle_hide_channel(
        self,
        user_id: int,
        channel_id: int
    ) -> Tuple[bool, bool]:
        """Toggle hide/unhide channel. Returns (success, is_now_hidden)"""
        is_hidden = await self.is_channel_hidden(user_id, channel_id)

        if is_hidden:
            # Unhide
            result = await self.session.execute(
                delete(HiddenChannel).where(
                    and_(
                        HiddenChannel.user_id == user_id,
                        HiddenChannel.channel_id == channel_id
                    )
                )
            )
            await self.session.commit()
            return True, False
        else:
            # Hide
            hidden = HiddenChannel(
                user_id=user_id,
                channel_id=channel_id,
                created_at=datetime.utcnow()
            )
            self.session.add(hidden)
            await self.session.commit()
            return True, True

    async def create_automatic_channel(
        self,
        name: str,
        creator_id: int,
        organization_id: Optional[int] = None,
        category: Optional[str] = None,
        language: str = "es"
    ) -> Channel:
        """Create a new automatic channel"""
        # Generate unique id_code
        id_code = f"auto_{secrets.token_urlsafe(8)}"

        channel = Channel(
            id_code=id_code,
            name=name,
            is_automatic=True,
            category=category,
            language=language,
            creator_id=creator_id,
            organization_id=organization_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def update_channel_metadata(
        self,
        channel_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update automatic channel metadata"""
        result = await self.session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        channel = result.scalar_one_or_none()

        if not channel:
            return False

        if name:
            channel.name = name
        if description is not None:
            channel.description = description

        channel.updated_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def delete_automatic_channel(self, channel_id: int) -> bool:
        """Delete an automatic channel"""
        result = await self.session.execute(
            select(Channel).where(
                and_(
                    Channel.id == channel_id,
                    Channel.is_automatic == True
                )
            )
        )
        channel = result.scalar_one_or_none()

        if not channel:
            return False

        await self.session.delete(channel)
        await self.session.commit()
        return True

    async def generate_web_access_token(
        self,
        user_id: int,
        base_url: str = "https://agape.penwin.cloud/prayer-life"
    ) -> PrayerLifeWebAccess:
        """Generate a temporary web access token"""
        token = secrets.token_urlsafe(32)
        web_url = f"{base_url}?token={token}"
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry

        access = PrayerLifeWebAccess(
            user_id=user_id,
            token=token,
            web_url=web_url,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        self.session.add(access)
        await self.session.commit()
        await self.session.refresh(access)
        return access
