"""Settings repository - Database operations"""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import select, func, and_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserSetting


class SettingsRepository:
    """Repository for user settings data operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # CREATE/UPDATE OPERATIONS
    # ============================================================

    async def set_setting(
        self,
        user_id: int,
        key: str,
        value: str
    ) -> UserSetting:
        """Create or update a user setting"""
        # Check if setting exists
        existing = await self.get_setting(user_id, key)

        if existing:
            # Update existing
            await self.session.execute(
                update(UserSetting)
                .where(
                    and_(
                        UserSetting.user_id == user_id,
                        UserSetting.key == key
                    )
                )
                .values(
                    value=value,
                    updated_at=datetime.utcnow()
                )
            )
            await self.session.commit()
            return await self.get_setting(user_id, key)
        else:
            # Create new
            setting = UserSetting(
                user_id=user_id,
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(setting)
            await self.session.commit()
            await self.session.refresh(setting)
            return setting

    async def set_multiple_settings(
        self,
        user_id: int,
        settings: Dict[str, str]
    ) -> List[UserSetting]:
        """Set multiple user settings at once"""
        result_settings = []
        for key, value in settings.items():
            setting = await self.set_setting(user_id, key, value)
            result_settings.append(setting)
        return result_settings

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    async def get_setting(
        self,
        user_id: int,
        key: str
    ) -> Optional[UserSetting]:
        """Get a specific user setting"""
        result = await self.session.execute(
            select(UserSetting)
            .where(
                and_(
                    UserSetting.user_id == user_id,
                    UserSetting.key == key
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_all_settings(
        self,
        user_id: int
    ) -> List[UserSetting]:
        """Get all settings for a user"""
        result = await self.session.execute(
            select(UserSetting)
            .where(UserSetting.user_id == user_id)
            .order_by(UserSetting.key)
        )
        return list(result.scalars().all())

    async def get_settings_dict(
        self,
        user_id: int
    ) -> Dict[str, str]:
        """Get all settings as key-value dictionary"""
        settings = await self.get_all_settings(user_id)
        return {s.key: s.value for s in settings}

    async def get_settings_count(self, user_id: int) -> int:
        """Get count of user settings"""
        result = await self.session.execute(
            select(func.count(UserSetting.id))
            .where(UserSetting.user_id == user_id)
        )
        return result.scalar() or 0

    # ============================================================
    # DELETE OPERATIONS
    # ============================================================

    async def delete_setting(
        self,
        user_id: int,
        key: str
    ) -> bool:
        """Delete a specific user setting"""
        result = await self.session.execute(
            delete(UserSetting)
            .where(
                and_(
                    UserSetting.user_id == user_id,
                    UserSetting.key == key
                )
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def delete_all_settings(self, user_id: int) -> int:
        """Delete all user settings"""
        result = await self.session.execute(
            delete(UserSetting)
            .where(UserSetting.user_id == user_id)
        )
        await self.session.commit()
        return result.rowcount
