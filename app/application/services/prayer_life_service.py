"""Prayer Life service - Business logic"""
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.application.repositories.prayer_life_repository import PrayerLifeRepository
from app.domain.schemas.prayer_life import (
    AutomaticChannelsResponse,
    AutomaticChannelCategory,
    AutomaticChannelResponse,
    AutomaticChannelContentResponse,
    SubscribeAutomaticChannelResponse,
    UpdateChannelOrderRequest,
    UpdateChannelOrderResponse,
    ToggleHideChannelRequest,
    ToggleHideChannelResponse,
    CreateAutomaticChannelRequest,
    CreateAutomaticChannelResponse,
    UpdateChannelMetadataRequest,
    UpdateChannelMetadataResponse,
    DeleteAutomaticChannelResponse,
    GenerateWebAccessResponse,
)


class PrayerLifeService:
    """Service for prayer life and automatic channels"""

    # Predefined categories for automatic channels
    CATEGORIES = {
        "readings": "Lecturas Diarias",
        "saints": "Santos del Día",
        "prayers": "Oraciones",
        "rosary": "Santo Rosario",
        "gospels": "Evangelio del Día",
        "psalms": "Salmos",
        "reflections": "Reflexiones",
        "other": "Otros"
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PrayerLifeRepository(session)

    async def get_automatic_channels(
        self,
        language: str = "es",
        user_id: Optional[int] = None
    ) -> AutomaticChannelsResponse:
        """Get all automatic channels organized by categories"""
        # Get all automatic channels
        channels = await self.repo.get_automatic_channels_by_language(language, user_id)

        # Organize by categories
        categories_dict: Dict[str, List] = {}

        for channel in channels:
            category_key = channel.category or "other"
            if category_key not in categories_dict:
                categories_dict[category_key] = []

            # Check subscription status
            is_subscribed = False
            is_hidden = False
            if user_id:
                is_subscribed = await self.repo.is_user_subscribed(user_id, channel.id)
                is_hidden = await self.repo.is_channel_hidden(user_id, channel.id)

            # Get content if available
            content_data = None
            has_content = False
            channel_content = await self.repo.get_channel_content(channel.id)
            if channel_content:
                has_content = True
                content_data = AutomaticChannelContentResponse(
                    title=channel_content.title,
                    text=channel_content.text,
                    audio_url=channel_content.audio_url,
                    name=channel_content.name,
                    biography=channel_content.biography,
                    image_url=channel_content.image_url
                )

            channel_response = AutomaticChannelResponse(
                id=channel.id,
                id_code=channel.id_code,
                name=channel.name,
                description=channel.description,
                image_url=channel.image_url,
                subscribed=is_subscribed,
                has_content=has_content,
                content=content_data
            )

            categories_dict[category_key].append(channel_response)

        # Build category responses
        categories = []
        for category_key, category_channels in categories_dict.items():
            category_name = self.CATEGORIES.get(category_key, "Otros")
            categories.append(AutomaticChannelCategory(
                id=category_key,
                name=category_name,
                channels=category_channels
            ))

        return AutomaticChannelsResponse(categories=categories)

    async def subscribe_automatic_channel(
        self,
        channel_id_code: str,
        user_id: int
    ) -> SubscribeAutomaticChannelResponse:
        """Subscribe/unsubscribe to automatic channel"""
        # Get channel
        channel = await self.repo.get_channel_by_id_code(channel_id_code)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        if not channel.is_automatic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Channel is not an automatic channel"
            )

        # Check if already subscribed
        is_subscribed = await self.repo.is_user_subscribed(user_id, channel.id)

        if is_subscribed:
            # Unsubscribe
            await self.repo.unsubscribe_from_channel(user_id, channel.id)
            return SubscribeAutomaticChannelResponse(success=True, subscribed=False)
        else:
            # Subscribe
            await self.repo.subscribe_to_channel(user_id, channel.id)
            return SubscribeAutomaticChannelResponse(success=True, subscribed=True)

    async def update_channel_order(
        self,
        request: UpdateChannelOrderRequest,
        user_id: int
    ) -> UpdateChannelOrderResponse:
        """Update user's custom channel order"""
        await self.repo.save_channel_order(user_id, request.channel_order)
        return UpdateChannelOrderResponse(success=True)

    async def toggle_hide_channel(
        self,
        request: ToggleHideChannelRequest,
        user_id: int
    ) -> ToggleHideChannelResponse:
        """Toggle hide/unhide channel"""
        # Get channel
        channel = await self.repo.get_channel_by_id_code(request.channel_id_code)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        success, is_hidden = await self.repo.toggle_hide_channel(user_id, channel.id)

        return ToggleHideChannelResponse(
            success=success,
            hidden=is_hidden
        )

    async def create_automatic_channel(
        self,
        request: CreateAutomaticChannelRequest,
        creator_id: int
    ) -> CreateAutomaticChannelResponse:
        """Create a new automatic channel"""
        channel = await self.repo.create_automatic_channel(
            name=request.name,
            creator_id=creator_id,
            organization_id=request.organization_id,
            category=request.category,
            language=request.language
        )

        return CreateAutomaticChannelResponse(
            success=True,
            channel_id=channel.id,
            id_code=channel.id_code
        )

    async def update_channel_metadata(
        self,
        request: UpdateChannelMetadataRequest
    ) -> UpdateChannelMetadataResponse:
        """Update automatic channel metadata"""
        success = await self.repo.update_channel_metadata(
            channel_id=request.channel_id,
            name=request.name,
            description=request.description
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        return UpdateChannelMetadataResponse(success=True)

    async def delete_automatic_channel(
        self,
        channel_id: int
    ) -> DeleteAutomaticChannelResponse:
        """Delete an automatic channel"""
        success = await self.repo.delete_automatic_channel(channel_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found or not an automatic channel"
            )

        return DeleteAutomaticChannelResponse(success=True)

    async def generate_web_access(
        self,
        user_id: int
    ) -> GenerateWebAccessResponse:
        """Generate temporary web access for prayer life"""
        access = await self.repo.generate_web_access_token(user_id)

        return GenerateWebAccessResponse(
            success=True,
            web_url=access.web_url,
            token=access.token,
            expires_at=access.expires_at
        )
