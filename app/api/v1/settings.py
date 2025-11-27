"""User Settings endpoints"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.settings_service import SettingsService
from app.domain.schemas.settings import (
    SetSettingRequest,
    SetMultipleSettingsRequest,
    SettingResponse,
    SettingsListResponse,
    SettingsDictResponse,
    SettingOperationResponse,
    SettingsDeleteResponse
)

router = APIRouter(tags=["Settings"], prefix="/settings")


# Dependency
async def get_settings_service(session: AsyncSession = Depends(get_db)) -> SettingsService:
    return SettingsService(session)


# ============================================================
# SET SETTINGS ENDPOINTS
# ============================================================

@router.post("", response_model=SettingOperationResponse, status_code=status.HTTP_200_OK)
async def set_setting(
    data: SetSettingRequest,
    current_user: User = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Set a user setting (create or update)

    **Examples of common settings:**
    - `theme`: "light" | "dark"
    - `language`: "en" | "es" | "ca"
    - `notifications_enabled`: "true" | "false"
    - `email_notifications`: "true" | "false"
    - `push_notifications`: "true" | "false"
    """
    return await settings_service.set_setting(
        user_id=current_user.id,
        key=data.key,
        value=data.value
    )


@router.post("/bulk", response_model=SettingsListResponse, status_code=status.HTTP_200_OK)
async def set_multiple_settings(
    data: SetMultipleSettingsRequest,
    current_user: User = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Set multiple user settings at once

    **Example:**
    ```json
    {
      "settings": {
        "theme": "dark",
        "language": "es",
        "notifications_enabled": "true"
      }
    }
    ```
    """
    return await settings_service.set_multiple_settings(
        user_id=current_user.id,
        settings=data.settings
    )


# ============================================================
# GET SETTINGS ENDPOINTS
# ============================================================

@router.get("/{key}", response_model=SettingResponse, status_code=status.HTTP_200_OK)
async def get_setting(
    key: str,
    current_user: User = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Get a specific user setting by key

    Returns 404 if setting not found
    """
    return await settings_service.get_setting(
        user_id=current_user.id,
        key=key
    )


@router.get("", response_model=SettingsListResponse, status_code=status.HTTP_200_OK)
async def get_all_settings(
    current_user: User = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Get all user settings

    Returns list of all settings with metadata (id, timestamps, etc.)
    """
    return await settings_service.get_all_settings(user_id=current_user.id)


@router.get("/dict/all", response_model=SettingsDictResponse, status_code=status.HTTP_200_OK)
async def get_settings_dict(
    current_user: User = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Get all user settings as a simple key-value dictionary

    Returns:
    ```json
    {
      "settings": {
        "theme": "dark",
        "language": "es",
        "notifications_enabled": "true"
      }
    }
    ```
    """
    return await settings_service.get_settings_dict(user_id=current_user.id)


# ============================================================
# DELETE SETTINGS ENDPOINTS
# ============================================================

@router.delete("/{key}", response_model=SettingsDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_setting(
    key: str,
    current_user: User = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Delete a specific user setting

    Returns 404 if setting not found
    """
    return await settings_service.delete_setting(
        user_id=current_user.id,
        key=key
    )


@router.delete("", response_model=SettingsDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_all_settings(
    current_user: User = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service)
):
    """
    Delete all user settings

    ⚠️ Warning: This will delete ALL user settings permanently
    """
    return await settings_service.delete_all_settings(user_id=current_user.id)
