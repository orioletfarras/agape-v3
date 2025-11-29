"""Organization repository for database operations"""
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserOrganization


class OrganizationRepository:
    """Repository for organization-related database operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_user_org_admin(
        self,
        user_id: int,
        organization_id: int
    ) -> bool:
        """Check if user is admin of organization"""
        result = await self.session.execute(
            select(UserOrganization).where(
                and_(
                    UserOrganization.user_id == user_id,
                    UserOrganization.organization_id == organization_id
                )
            )
        )
        user_org = result.scalar_one_or_none()
        return user_org is not None
