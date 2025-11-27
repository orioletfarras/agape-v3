"""Debug schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SaveLogsRequest(BaseModel):
    """Request to save client logs"""
    logs: List[str] = Field(..., description="Array of log messages")
    log_level: Optional[str] = Field(default="info", description="Log level: info, warning, error, debug")
    source: Optional[str] = Field(default="mobile", description="Source: mobile, web, etc.")
    context: Optional[str] = Field(None, description="Additional context as JSON string")
    device_info: Optional[str] = Field(None, description="Device information as JSON string")


class DebugLogResponse(BaseModel):
    """Debug log response"""
    id: int
    user_id: Optional[int] = None
    log_level: str
    message: str
    context: Optional[str] = None
    source: Optional[str] = None
    device_info: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GetLogsResponse(BaseModel):
    """Response for getting logs"""
    logs: List[str]
    total: int = 0


class DeleteLogsResponse(BaseModel):
    """Response for deleting logs"""
    success: bool
    deleted_count: int = 0
    message: str = "Logs deleted successfully"
