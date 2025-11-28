"""User profile service with business logic"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, UploadFile

from app.infrastructure.database.models import User, UserSetting, Organization
from app.infrastructure.aws import s3_service

logger = logging.getLogger(__name__)


class UserService:
    """User service"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_profile(self, user_id: int) -> User:
        """Get user profile"""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    async def upload_profile_image(self, user_id: int, file: UploadFile) -> Dict[str, Any]:
        """Upload and update profile image"""
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image",
            )

        # Get user first to get id_code
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Read file data
        file_data = await file.read()

        # Upload to S3 with user_id (convert to string for S3 path)
        image_url = await s3_service.upload_profile_image(str(user.id), file_data)

        # Delete old image if exists
        if user.profile_image_url:
            await s3_service.delete_file(user.profile_image_url)

        # Update user profile image
        user.profile_image_url = image_url
        await self.session.commit()

        return {
            "success": True,
            "image_url": image_url,
        }

    async def update_personal_info(
        self,
        user_id: int,
        nombre: Optional[str] = None,
        apellidos: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update personal information"""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Update fields
        if nombre is not None:
            user.nombre = nombre
        if apellidos is not None:
            user.apellidos = apellidos
        if bio is not None:
            user.bio = bio

        await self.session.commit()

        return {"success": True}

    async def get_personal_info(self, user_id: int) -> Dict[str, Any]:
        """Get personal information"""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {
            "nombre": user.nombre,
            "apellidos": user.apellidos,
            "email": user.email,
            "fecha_nacimiento": user.fecha_nacimiento,
            "genero": user.genero,
            "telefono": user.telefono,
        }

    async def update_user_setting(
        self,
        user_id: int,
        key: str,
        value: str,
    ) -> Dict[str, Any]:
        """Update or create user setting"""
        # Check if setting exists
        result = await self.session.execute(
            select(UserSetting).where(
                UserSetting.user_id == user_id,
                UserSetting.key == key,
            )
        )
        setting = result.scalar_one_or_none()

        if setting:
            # Update existing setting
            setting.value = value
        else:
            # Create new setting
            setting = UserSetting(
                user_id=user_id,
                key=key,
                value=value,
            )
            self.session.add(setting)

        await self.session.commit()

        return {"success": True}

    async def check_nickname(self, nickname: str) -> Dict[str, Any]:
        """Check if nickname/username is available"""
        result = await self.session.execute(
            select(User).where(User.username == nickname)
        )
        user = result.scalar_one_or_none()

        return {"available": user is None}

    async def complete_profile(
        self,
        user_id: int,
        nickname: str,
        parish_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Complete user profile (onboarding)"""
        # Check if username is available
        result = await self.session.execute(
            select(User).where(User.username == nickname)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

        # Get user
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Update user
        user.username = nickname
        if parish_id:
            user.parish_id = parish_id
        user.onboarding_completed = True

        await self.session.commit()

        return {"success": True}

    async def get_primary_organization(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's primary organization"""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.primary_organization_id:
            return None

        # Get organization
        result = await self.session.execute(
            select(Organization).where(Organization.id == user.primary_organization_id)
        )
        org = result.scalar_one_or_none()

        if not org:
            return None

        return {
            "id": org.id,
            "name": org.name,
            "image_url": org.image_url,
        }

    async def update_primary_organization(
        self,
        user_id: int,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Update user's primary organization"""
        # Check if organization exists
        result = await self.session.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Get user
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Update primary organization
        user.primary_organization_id = organization_id
        await self.session.commit()

        return {"success": True}
