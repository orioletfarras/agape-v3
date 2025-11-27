"""Settings business logic service"""
from typing import Dict
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.settings_repository import SettingsRepository
from app.domain.schemas.settings import (
    SettingResponse,
    SettingsListResponse,
    SettingsDictResponse,
    SettingOperationResponse,
    SettingsDeleteResponse
)


class SettingsService:
    """Service for user settings business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SettingsRepository(session)

    async def set_setting(
        self,
        user_id: int,
        key: str,
        value: str
    ) -> SettingOperationResponse:
        """Set a user setting"""
        setting = await self.repo.set_setting(user_id, key, value)

        return SettingOperationResponse(
            success=True,
            message=f"Setting '{key}' updated successfully",
            setting=SettingResponse(
                id=setting.id,
                user_id=setting.user_id,
                key=setting.key,
                value=setting.value,
                created_at=setting.created_at,
                updated_at=setting.updated_at
            )
        )

    async def set_multiple_settings(
        self,
        user_id: int,
        settings: Dict[str, str]
    ) -> SettingsListResponse:
        """Set multiple user settings"""
        result_settings = await self.repo.set_multiple_settings(user_id, settings)

        setting_responses = [
            SettingResponse(
                id=s.id,
                user_id=s.user_id,
                key=s.key,
                value=s.value,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in result_settings
        ]

        return SettingsListResponse(
            settings=setting_responses,
            total=len(setting_responses)
        )

    async def get_setting(
        self,
        user_id: int,
        key: str
    ) -> SettingResponse:
        """Get a specific user setting"""
        setting = await self.repo.get_setting(user_id, key)

        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )

        return SettingResponse(
            id=setting.id,
            user_id=setting.user_id,
            key=setting.key,
            value=setting.value,
            created_at=setting.created_at,
            updated_at=setting.updated_at
        )

    async def get_all_settings(
        self,
        user_id: int
    ) -> SettingsListResponse:
        """Get all settings for a user"""
        settings = await self.repo.get_all_settings(user_id)

        setting_responses = [
            SettingResponse(
                id=s.id,
                user_id=s.user_id,
                key=s.key,
                value=s.value,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in settings
        ]

        return SettingsListResponse(
            settings=setting_responses,
            total=len(setting_responses)
        )

    async def get_settings_dict(
        self,
        user_id: int
    ) -> SettingsDictResponse:
        """Get all settings as key-value dictionary"""
        settings_dict = await self.repo.get_settings_dict(user_id)

        return SettingsDictResponse(
            settings=settings_dict
        )

    async def delete_setting(
        self,
        user_id: int,
        key: str
    ) -> SettingsDeleteResponse:
        """Delete a specific user setting"""
        success = await self.repo.delete_setting(user_id, key)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )

        return SettingsDeleteResponse(
            success=True,
            message=f"Setting '{key}' deleted successfully",
            deleted_count=1
        )

    async def delete_all_settings(
        self,
        user_id: int
    ) -> SettingsDeleteResponse:
        """Delete all user settings"""
        deleted_count = await self.repo.delete_all_settings(user_id)

        return SettingsDeleteResponse(
            success=True,
            message=f"Deleted {deleted_count} settings",
            deleted_count=deleted_count
        )
