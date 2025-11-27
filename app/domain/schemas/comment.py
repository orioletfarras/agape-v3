"""Comment domain schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreateCommentRequest(BaseModel):
    """Request to create a comment"""
    post_id: int
    content: str = Field(..., min_length=1, max_length=2000)


class UpdateCommentRequest(BaseModel):
    """Request to update a comment"""
    content: str = Field(..., min_length=1, max_length=2000)


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

    model_config = ConfigDict(from_attributes=True)


class CommentResponse(BaseModel):
    """Comment response"""
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    # User info
    user: Optional[UserBasicResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CommentListResponse(BaseModel):
    """Paginated list of comments"""
    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class CommentDeleteResponse(BaseModel):
    """Response after deleting comment"""
    success: bool
    message: str
