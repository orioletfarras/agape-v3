"""Social domain schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class FollowUserRequest(BaseModel):
    """Request to follow a user"""
    user_id: int


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class UserBasicResponse(BaseModel):
    """Basic user info"""
    id: int
    username: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None

    # Social counts
    followers_count: int = 0
    following_count: int = 0

    # Current user status
    is_following: bool = False
    is_followed_by: bool = False

    model_config = ConfigDict(from_attributes=True)


class FollowResponse(BaseModel):
    """Follow/unfollow response"""
    success: bool
    is_following: bool
    message: str


class UserListResponse(BaseModel):
    """Paginated list of users"""
    users: List[UserBasicResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class FollowingResponse(BaseModel):
    """Following relationship info"""
    id: int
    follower_id: int
    following_id: int
    created_at: datetime
    user: Optional[UserBasicResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SocialStatsResponse(BaseModel):
    """Social statistics for a user"""
    user_id: int
    followers_count: int
    following_count: int
    posts_count: int
