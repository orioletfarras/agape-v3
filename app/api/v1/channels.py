"""Channels endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.channel_service import ChannelService
from app.infrastructure.aws.s3_service import S3Service
from app.domain.schemas.channel import (
    CreateChannelRequest,
    UpdateChannelRequest,
    SubscribeChannelRequest,
    UpdateChannelSettingsRequest,
    AddChannelAdminRequest,
    CreateChannelAlertRequest,
    ChannelResponse,
    ChannelDetailResponse,
    ChannelListResponse,
    ChannelSubscriptionResponse,
    ChannelSettingsResponse,
    ChannelDeleteResponse
)

router = APIRouter(tags=["Channels"], prefix="/channels")


# Dependency to get channel service
async def get_channel_service(session: AsyncSession = Depends(get_db)) -> ChannelService:
    return ChannelService(session)


# ============================================================
# CHANNEL CRUD ENDPOINTS
# ============================================================

@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    data: CreateChannelRequest,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Create a new channel

    **Requirements:**
    - Must be authenticated
    - User becomes admin automatically
    - User is subscribed automatically

    **Fields:**
    - name: Channel name (required)
    - description: Channel description (optional)
    - organization_id: Organization ID (required)
    - image_url: Channel image URL (optional)
    - is_private: Whether channel is private (default: false)
    """
    return await channel_service.create_channel(
        user_id=current_user.id,
        name=data.name,
        organization_id=data.organization_id,
        description=data.description,
        image_url=data.image_url
    )


@router.get("", response_model=ChannelListResponse, status_code=status.HTTP_200_OK)
async def get_channels(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    subscribed_only: bool = Query(True, description="Only show subscribed channels"),
    include_hidden: bool = Query(False, description="Include hidden channels"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get list of channels

    **Filters:**
    - organization_id: Filter by organization
    - subscribed_only: Only show channels user is subscribed to
    - include_hidden: Include channels user has hidden
    - search: Search in channel name or description
    - page: Pagination page number
    - page_size: Number of channels per page (max 100)
    """
    return await channel_service.get_channels(
        user_id=current_user.id,
        organization_id=organization_id,
        subscribed_only=subscribed_only,
        include_hidden=include_hidden,
        search=search,
        page=page,
        page_size=page_size
    )


@router.get("/{channel_id}", response_model=ChannelDetailResponse, status_code=status.HTTP_200_OK)
async def get_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get a single channel by ID

    Returns complete channel data including:
    - Channel info (name, description, image, privacy)
    - Organization information
    - Statistics (subscribers, posts, events count)
    - Current user status (subscribed, admin, hidden)
    """
    return await channel_service.get_channel_by_id(channel_id, current_user.id)


@router.put("/{channel_id}", response_model=ChannelResponse, status_code=status.HTTP_200_OK)
async def update_channel(
    channel_id: int,
    data: UpdateChannelRequest,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Update a channel

    **Requirements:**
    - Only channel admins can update

    **Updatable fields:**
    - name
    - description
    - image_url
    - is_private
    """
    return await channel_service.update_channel(
        channel_id=channel_id,
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        image_url=data.image_url,
        is_private=data.is_private
    )


@router.delete("/{channel_id}", response_model=ChannelDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Delete a channel

    **Requirements:**
    - Only channel admins can delete
    - Deletes all related data (subscriptions, posts, events, etc.)
    """
    return await channel_service.delete_channel(channel_id, current_user.id)


# ============================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================

@router.post("/{channel_id}/subscribe", response_model=ChannelSubscriptionResponse, status_code=status.HTTP_200_OK)
async def subscribe_to_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Subscribe to a channel

    After subscribing, user will see posts and events from this channel
    """
    return await channel_service.subscribe_to_channel(current_user.id, channel_id)


@router.delete("/{channel_id}/subscribe", response_model=ChannelSubscriptionResponse, status_code=status.HTTP_200_OK)
async def unsubscribe_from_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Unsubscribe from a channel

    User will no longer see posts and events from this channel
    """
    return await channel_service.unsubscribe_from_channel(current_user.id, channel_id)


@router.get("/{channel_id}/subscribers", status_code=status.HTTP_200_OK)
async def get_channel_subscribers(
    channel_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get list of channel subscribers

    **Requirements:**
    - Only channel admins can view subscribers

    Returns paginated list of subscribers with user information
    """
    return await channel_service.get_channel_subscribers(
        channel_id, current_user.id, page, page_size
    )


@router.get("/my/subscriptions", response_model=ChannelListResponse, status_code=status.HTTP_200_OK)
async def get_my_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get channels current user is subscribed to

    Returns paginated list of subscribed channels
    """
    return await channel_service.get_user_subscriptions(
        current_user.id, page, page_size
    )


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@router.post("/{channel_id}/admins", status_code=status.HTTP_200_OK)
async def add_channel_admin(
    channel_id: int,
    data: AddChannelAdminRequest,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Add a channel admin

    **Requirements:**
    - Only existing channel admins can add new admins
    """
    return await channel_service.add_channel_admin(
        channel_id, current_user.id, data.user_id
    )


@router.delete("/{channel_id}/admins/{user_id}", status_code=status.HTTP_200_OK)
async def remove_channel_admin(
    channel_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Remove a channel admin

    **Requirements:**
    - Only existing channel admins can remove admins
    """
    return await channel_service.remove_channel_admin(
        channel_id, current_user.id, user_id
    )


@router.get("/{channel_id}/admins", status_code=status.HTTP_200_OK)
async def get_channel_admins(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get list of channel admins

    Returns all admins with their user information
    """
    return await channel_service.get_channel_admins(channel_id)


# ============================================================
# SETTINGS ENDPOINTS
# ============================================================

@router.get("/{channel_id}/settings", response_model=ChannelSettingsResponse, status_code=status.HTTP_200_OK)
async def get_channel_settings(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get notification settings for a channel

    Returns user's notification preferences for this channel
    """
    return await channel_service.get_channel_settings(current_user.id, channel_id)


@router.put("/{channel_id}/settings", response_model=ChannelSettingsResponse, status_code=status.HTTP_200_OK)
async def update_channel_settings(
    channel_id: int,
    data: UpdateChannelSettingsRequest,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Update notification settings for a channel

    **Settings:**
    - notifications_enabled: Enable/disable all notifications
    - post_notifications: Enable/disable post notifications
    - event_notifications: Enable/disable event notifications
    """
    return await channel_service.update_channel_settings(
        user_id=current_user.id,
        channel_id=channel_id,
        notifications_enabled=data.notifications_enabled,
        post_notifications=data.post_notifications,
        event_notifications=data.event_notifications
    )


# ============================================================
# HIDE/UNHIDE ENDPOINTS
# ============================================================

@router.post("/{channel_id}/hide", status_code=status.HTTP_200_OK)
async def hide_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Hide a channel

    Hidden channels won't appear in channel lists unless include_hidden=true
    """
    return await channel_service.hide_channel(current_user.id, channel_id)


@router.delete("/{channel_id}/hide", status_code=status.HTTP_200_OK)
async def unhide_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Unhide a previously hidden channel
    """
    return await channel_service.unhide_channel(current_user.id, channel_id)


# ============================================================
# ALERTS ENDPOINTS
# ============================================================

@router.post("/{channel_id}/alerts", status_code=status.HTTP_201_CREATED)
async def create_channel_alert(
    channel_id: int,
    data: CreateChannelAlertRequest,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Create a channel alert

    **Requirements:**
    - Only channel admins can create alerts

    Alerts are sent as push notifications to all channel subscribers
    """
    return await channel_service.create_channel_alert(
        channel_id=channel_id,
        user_id=current_user.id,
        title=data.title,
        message=data.message
    )


@router.get("/{channel_id}/alerts", status_code=status.HTTP_200_OK)
async def get_channel_alerts(
    channel_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get alerts for a channel

    Returns paginated list of channel alerts
    """
    return await channel_service.get_channel_alerts(channel_id, page, page_size)


# ============================================================
# STATISTICS ENDPOINTS
# ============================================================

@router.get("/{channel_id}/stats", status_code=status.HTTP_200_OK)
async def get_channel_stats(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get statistics for a channel

    Returns:
    - subscribers_count: Number of subscribers
    - posts_count: Number of posts
    - events_count: Number of events
    - admins_count: Number of admins
    """
    return await channel_service.get_channel_stats(channel_id)


# ============================================================
# IMAGE UPLOAD ENDPOINTS
# ============================================================

@router.post("/upload-image", status_code=status.HTTP_200_OK)
async def upload_channel_image(
    file: UploadFile = File(..., description="Channel image file"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Upload a channel image

    **Requirements:**
    - Must be authenticated
    - Supported formats: JPEG, PNG, JPG, WEBP
    - Max file size: 10MB
    - Image will be optimized and resized

    **Returns:**
    - image_url: URL of the uploaded image on S3

    **Usage:**
    1. Upload image using this endpoint
    2. Use returned URL in CreateChannelRequest.image_url
    """
    s3_service = S3Service()

    # Read file data
    file_data = await file.read()

    # Upload to S3
    url = await s3_service.upload_channel_image(file_data)

    return {
        "success": True,
        "image_url": url
    }


# ============================================================
# ORGANIZATION CHANNELS ENDPOINTS
# ============================================================

@router.get("/organization/{organization_id}", response_model=ChannelListResponse, status_code=status.HTTP_200_OK)
async def get_organization_channels(
    organization_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Get all channels for a specific organization

    Returns paginated list of channels from the organization
    """
    return await channel_service.get_channels(
        user_id=current_user.id,
        organization_id=organization_id,
        page=page,
        page_size=page_size
    )


# ============================================================
# SEARCH ENDPOINTS
# ============================================================

@router.get("/search/{query}", response_model=ChannelListResponse, status_code=status.HTTP_200_OK)
async def search_channels(
    query: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Search channels by name or description

    Searches in both channel name and description fields
    """
    return await channel_service.get_channels(
        user_id=current_user.id,
        search=query,
        page=page,
        page_size=page_size
    )
