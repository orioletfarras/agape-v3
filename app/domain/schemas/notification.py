"""Notification domain schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreateNotificationRequest(BaseModel):
    """Request to create a notification"""
    user_id: int
    type: str = Field(..., pattern="^(like|comment|follow|event|post|channel)$")
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    related_id: Optional[int] = None
    image_url: Optional[str] = None


class MarkNotificationReadRequest(BaseModel):
    """Request to mark notification as read"""
    notification_id: int


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class NotificationResponse(BaseModel):
    """Notification response"""
    id: int
    user_id: int
    type: str
    title: str
    message: str
    related_id: Optional[int] = None
    image_url: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Paginated list of notifications"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    has_more: bool


class NotificationStatsResponse(BaseModel):
    """Notification statistics"""
    total_count: int
    unread_count: int
    read_count: int


class NotificationMarkReadResponse(BaseModel):
    """Response for marking notification as read"""
    success: bool
    message: str


class NotificationDeleteResponse(BaseModel):
    """Response for deleting notification"""
    success: bool
    message: str
