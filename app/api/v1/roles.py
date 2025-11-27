"""Roles and permissions endpoints"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User, ChannelAdmin
from app.api.dependencies import get_current_user

router = APIRouter(tags=["Roles"], prefix="")


@router.get("/roles", status_code=status.HTTP_200_OK)
async def get_user_roles(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get user roles and permissions

    **Response:**
    ```json
    {
      "roles": ["user", "channel_admin"],
      "is_super_admin": false,
      "organizations_admin": [1, 2],
      "channels_admin": [5, 10, 15]
    }
    ```
    """
    # Get channels where user is admin
    result = await session.execute(
        select(ChannelAdmin.channel_id).where(ChannelAdmin.user_id == current_user.id)
    )
    channels_admin = [row[0] for row in result.all()]

    # Build roles list
    roles = ["user"]
    if channels_admin:
        roles.append("channel_admin")

    # Check if super admin (you can add a field to User model)
    is_super_admin = getattr(current_user, 'is_super_admin', False)
    if is_super_admin:
        roles.append("super_admin")

    return {
        "roles": roles,
        "is_super_admin": is_super_admin,
        "organizations_admin": [],  # Can be extended with organization admins
        "channels_admin": channels_admin
    }
