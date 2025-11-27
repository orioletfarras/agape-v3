"""Notification repository - Database operations"""
from typing import Tuple, List, Optional
from datetime import datetime
from sqlalchemy import select, func, and_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import Notification


class NotificationRepository:
    """Repository for notification data operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # CREATE OPERATIONS
    # ============================================================

    async def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        related_id: Optional[int] = None,
        image_url: Optional[str] = None
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            related_id=related_id,
            image_url=image_url,
            is_read=False,
            created_at=datetime.utcnow()
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    async def get_notification_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def get_user_notifications(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False
    ) -> Tuple[List[Notification], int]:
        """Get user's notifications with pagination"""
        # Build query
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)

        # Count total
        count_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)
        if unread_only:
            count_query = count_query.where(Notification.is_read == False)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get notifications
        query = (
            query
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        notifications = result.scalars().all()

        return list(notifications), total

    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        result = await self.session.execute(
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        return result.scalar() or 0

    async def get_notification_stats(self, user_id: int) -> dict:
        """Get notification statistics"""
        # Total count
        total_result = await self.session.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
        )
        total = total_result.scalar() or 0

        # Unread count
        unread_result = await self.session.execute(
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        unread = unread_result.scalar() or 0

        return {
            "total_count": total,
            "unread_count": unread,
            "read_count": total - unread
        }

    # ============================================================
    # UPDATE OPERATIONS
    # ============================================================

    async def mark_as_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        result = await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all user notifications as read"""
        result = await self.session.execute(
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
            .values(is_read=True)
        )
        await self.session.commit()
        return result.rowcount

    # ============================================================
    # DELETE OPERATIONS
    # ============================================================

    async def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification"""
        result = await self.session.execute(
            delete(Notification).where(Notification.id == notification_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def delete_all_notifications(self, user_id: int) -> int:
        """Delete all user notifications"""
        result = await self.session.execute(
            delete(Notification).where(Notification.user_id == user_id)
        )
        await self.session.commit()
        return result.rowcount
