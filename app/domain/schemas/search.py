"""Search domain schemas"""
from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class UserSearchResult(BaseModel):
    """User search result"""
    id: int
    username: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    type: str = "user"

    model_config = ConfigDict(from_attributes=True)


class PostSearchResult(BaseModel):
    """Post search result"""
    id: int
    content: str
    author_id: int
    author_username: Optional[str] = None
    channel_id: Optional[int] = None
    created_at: datetime
    type: str = "post"

    model_config = ConfigDict(from_attributes=True)


class ChannelSearchResult(BaseModel):
    """Channel search result"""
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    organization_id: Optional[int] = None
    subscribers_count: int = 0
    type: str = "channel"

    model_config = ConfigDict(from_attributes=True)


class EventSearchResult(BaseModel):
    """Event search result"""
    id: int
    name: str
    description: Optional[str] = None
    event_date: datetime
    location: Optional[str] = None
    channel_id: Optional[int] = None
    type: str = "event"

    model_config = ConfigDict(from_attributes=True)


class SearchResultsResponse(BaseModel):
    """Combined search results"""
    users: List[UserSearchResult]
    posts: List[PostSearchResult]
    channels: List[ChannelSearchResult]
    events: List[EventSearchResult]
    total_results: int


class UserSearchResponse(BaseModel):
    """User search results with pagination"""
    users: List[UserSearchResult]
    total: int
    page: int
    page_size: int
    has_more: bool


class PostSearchResponse(BaseModel):
    """Post search results with pagination"""
    posts: List[PostSearchResult]
    total: int
    page: int
    page_size: int
    has_more: bool


class ChannelSearchResponse(BaseModel):
    """Channel search results with pagination"""
    channels: List[ChannelSearchResult]
    total: int
    page: int
    page_size: int
    has_more: bool


class EventSearchResponse(BaseModel):
    """Event search results with pagination"""
    events: List[EventSearchResult]
    total: int
    page: int
    page_size: int
    has_more: bool
