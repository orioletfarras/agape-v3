"""Prayer Life schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AutomaticChannelContentResponse(BaseModel):
    """Content for automatic channels"""
    title: Optional[str] = None
    text: Optional[str] = None
    audio_url: Optional[str] = None
    name: Optional[str] = None  # For saints
    biography: Optional[str] = None  # For saints
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class AutomaticChannelResponse(BaseModel):
    """Automatic channel info"""
    id: int
    id_code: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    subscribed: bool = False
    has_content: bool = False
    content: Optional[AutomaticChannelContentResponse] = None

    class Config:
        from_attributes = True


class AutomaticChannelCategory(BaseModel):
    """Category of automatic channels"""
    id: str
    name: str
    channels: List[AutomaticChannelResponse] = []


class AutomaticChannelsResponse(BaseModel):
    """Response for automatic channels endpoint"""
    categories: List[AutomaticChannelCategory]


class SubscribeAutomaticChannelResponse(BaseModel):
    """Response for subscribe/unsubscribe"""
    success: bool
    subscribed: bool


class UpdateChannelOrderRequest(BaseModel):
    """Request to update channel order"""
    channel_order: List[str] = Field(..., description="Array of channel id_codes in desired order")


class UpdateChannelOrderResponse(BaseModel):
    """Response for channel order update"""
    success: bool


class ToggleHideChannelRequest(BaseModel):
    """Request to toggle hide channel"""
    channel_id_code: str


class ToggleHideChannelResponse(BaseModel):
    """Response for toggle hide"""
    success: bool
    hidden: bool


class CreateAutomaticChannelRequest(BaseModel):
    """Request to create automatic channel"""
    name: str = Field(..., min_length=1, max_length=255)
    organization_id: Optional[int] = None
    category: Optional[str] = Field(None, description="Category: readings, saints, prayers, etc.")
    language: str = Field(default="es", description="Language code")


class CreateAutomaticChannelResponse(BaseModel):
    """Response for create automatic channel"""
    success: bool
    channel_id: int
    id_code: str


class UpdateChannelMetadataRequest(BaseModel):
    """Request to update channel metadata"""
    channel_id: int
    name: str
    description: Optional[str] = None


class UpdateChannelMetadataResponse(BaseModel):
    """Response for update metadata"""
    success: bool


class DeleteAutomaticChannelResponse(BaseModel):
    """Response for delete automatic channel"""
    success: bool


class GenerateWebAccessResponse(BaseModel):
    """Response for generating web access"""
    success: bool
    web_url: str
    token: str
    expires_at: datetime
