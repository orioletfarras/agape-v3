"""Post domain schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreatePostRequest(BaseModel):
    """Request to create a new post"""
    channel_id: int = Field(..., description="Channel where the post will be created")
    content: str = Field(..., min_length=1, max_length=10000, description="Post content")
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    videos: Optional[List[str]] = Field(None, description="List of video URLs")
    event_id: Optional[int] = Field(None, description="Related event ID if applicable")


class UpdatePostRequest(BaseModel):
    """Request to update a post"""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None


class PostReactionRequest(BaseModel):
    """Request to add/remove reaction to a post"""
    action: str = Field(..., pattern="^(like|unlike|pray|unpray|favorite|unfavorite)$")


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class PostAuthorResponse(BaseModel):
    """Post author info"""
    id: int
    username: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    profile_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostChannelResponse(BaseModel):
    """Post channel info"""
    id: int
    name: str
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostEventResponse(BaseModel):
    """Post related event info"""
    id: int
    name: str
    event_date: datetime
    location: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostResponse(BaseModel):
    """Complete post response"""
    id: int
    channel_id: int
    author_id: int
    content: str
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    event_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Counts
    likes_count: int = 0
    prays_count: int = 0
    favorites_count: int = 0
    comments_count: int = 0

    # Current user reactions
    is_liked: bool = False
    is_prayed: bool = False
    is_favorited: bool = False
    is_hidden: bool = False

    # Related data
    author: Optional[PostAuthorResponse] = None
    channel: Optional[PostChannelResponse] = None
    event: Optional[PostEventResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    """Paginated list of posts"""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class PostStatsResponse(BaseModel):
    """Post statistics"""
    likes_count: int
    prays_count: int
    favorites_count: int
    comments_count: int


class PostReactionResponse(BaseModel):
    """Response after reaction action"""
    success: bool
    action: str
    new_count: int


class PostDeleteResponse(BaseModel):
    """Response after deleting post"""
    success: bool
    message: str


# ============================================================
# FILTER/QUERY SCHEMAS
# ============================================================

class PostFilters(BaseModel):
    """Filters for listing posts"""
    channel_id: Optional[int] = None
    author_id: Optional[int] = None
    event_id: Optional[int] = None
    include_hidden: bool = False
    only_favorites: bool = False
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
