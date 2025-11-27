"""Settings domain schemas"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class SetSettingRequest(BaseModel):
    """Request to set a user setting"""
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., max_length=10000)


class SetMultipleSettingsRequest(BaseModel):
    """Request to set multiple user settings"""
    settings: Dict[str, str] = Field(..., description="Key-value pairs of settings")


class DeleteSettingRequest(BaseModel):
    """Request to delete a setting"""
    key: str = Field(..., min_length=1, max_length=100)


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class SettingResponse(BaseModel):
    """Single setting response"""
    id: int
    user_id: int
    key: str
    value: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingsListResponse(BaseModel):
    """List of user settings"""
    settings: List[SettingResponse]
    total: int


class SettingsDictResponse(BaseModel):
    """Settings as key-value dictionary"""
    settings: Dict[str, str]


class SettingOperationResponse(BaseModel):
    """Response for setting operations"""
    success: bool
    message: str
    setting: Optional[SettingResponse] = None


class SettingsDeleteResponse(BaseModel):
    """Response for deleting settings"""
    success: bool
    message: str
    deleted_count: int = 0
