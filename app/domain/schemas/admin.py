"""Admin domain schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreateMessageReportRequest(BaseModel):
    """Request to report a message"""
    message_id: int
    reason: str = Field(..., min_length=1, max_length=1000)


class ResolveReportRequest(BaseModel):
    """Request to resolve a report"""
    status: str = Field(..., pattern="^(reviewed|resolved)$")


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


class MessageReportResponse(BaseModel):
    """Message report response"""
    id: int
    message_id: int
    reporter_id: int
    reason: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    reporter: Optional[UserBasicResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ReportListResponse(BaseModel):
    """Paginated list of reports"""
    reports: List[MessageReportResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ReportOperationResponse(BaseModel):
    """Response for report operations"""
    success: bool
    message: str
    report: Optional[MessageReportResponse] = None


class GlobalStatsResponse(BaseModel):
    """Global platform statistics"""
    total_users: int
    total_posts: int
    total_channels: int
    total_events: int
    total_messages: int
    total_comments: int
    total_reports_pending: int


class UserStatsResponse(BaseModel):
    """Detailed user statistics"""
    user_id: int
    posts_count: int
    comments_count: int
    followers_count: int
    following_count: int
    channels_created: int
    events_created: int
    messages_sent: int
