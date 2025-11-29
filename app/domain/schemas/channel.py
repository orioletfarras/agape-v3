"""Channel domain schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreateChannelRequest(BaseModel):
    """Request to create a new channel"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    organization_id: int
    image_url: Optional[str] = None
    is_private: bool = False


class UpdateChannelRequest(BaseModel):
    """Request to update a channel"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    image_url: Optional[str] = None
    is_private: Optional[bool] = None


class SubscribeChannelRequest(BaseModel):
    """Request to subscribe to a channel"""
    channel_id: int


class UpdateChannelSettingsRequest(BaseModel):
    """Request to update channel notification settings"""
    notifications_enabled: bool
    post_notifications: bool
    event_notifications: bool


class AddChannelAdminRequest(BaseModel):
    """Request to add a channel admin"""
    user_id: int


class CreateChannelAlertRequest(BaseModel):
    """Request to create a channel alert"""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    channel_id: int


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class ChannelResponse(BaseModel):
    """Basic channel response"""
    id: int
    name: str
    description: Optional[str] = None
    organization_id: int
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Counts
    subscribers_count: int = 0
    posts_count: int = 0
    events_count: int = 0

    # Current user status
    is_subscribed: bool = False
    is_admin: bool = False
    is_hidden: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChannelDetailResponse(ChannelResponse):
    """Detailed channel response with organization info"""
    organization: Optional["OrganizationResponse"] = None
    monthly_donation: float = 0


class OrganizationResponse(BaseModel):
    """Organization info for channel"""
    id: int
    name: str
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChannelListResponse(BaseModel):
    """Paginated list of channels"""
    channels: List[ChannelResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ChannelSubscriptionResponse(BaseModel):
    """Response after subscription action"""
    success: bool
    is_subscribed: bool
    message: str


class ChannelSettingsResponse(BaseModel):
    """Channel notification settings"""
    id: int
    channel_id: int
    user_id: int
    notifications_enabled: bool
    post_notifications: bool
    event_notifications: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChannelAdminResponse(BaseModel):
    """Channel admin info"""
    id: int
    channel_id: int
    user_id: int
    user: Optional["UserBasicResponse"] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBasicResponse(BaseModel):
    """Basic user info"""
    id: int
    username: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    profile_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChannelSubscriberResponse(BaseModel):
    """Channel subscriber info"""
    id: int
    channel_id: int
    user_id: int
    user: Optional[UserBasicResponse] = None
    subscribed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChannelAlertResponse(BaseModel):
    """Channel alert response"""
    id: int
    channel_id: int
    title: str
    message: str
    created_by: int
    created_at: datetime
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChannelStatsResponse(BaseModel):
    """Channel statistics"""
    subscribers_count: int
    posts_count: int
    events_count: int
    admins_count: int


class ChannelDeleteResponse(BaseModel):
    """Response after deleting channel"""
    success: bool
    message: str


# ============================================================
# FILTER/QUERY SCHEMAS
# ============================================================

class ChannelFilters(BaseModel):
    """Filters for listing channels"""
    organization_id: Optional[int] = None
    is_private: Optional[bool] = None
    subscribed_only: bool = False
    include_hidden: bool = False
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
