"""Notification business logic service"""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.notification_repository import NotificationRepository
from app.domain.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationStatsResponse,
    NotificationMarkReadResponse,
    NotificationDeleteResponse
)


class NotificationService:
    """Service for notification business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NotificationRepository(session)

    async def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        related_id: Optional[int] = None,
        image_url: Optional[str] = None
    ) -> NotificationResponse:
        """Create a new notification"""
        notification = await self.repo.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_id=related_id,
            image_url=image_url
        )

        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            related_id=notification.related_id,
            image_url=notification.image_url,
            is_read=notification.is_read,
            created_at=notification.created_at
        )

    async def get_user_notifications(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False
    ) -> NotificationListResponse:
        """Get user's notifications"""
        notifications, total = await self.repo.get_user_notifications(
            user_id=user_id,
            page=page,
            page_size=page_size,
            unread_only=unread_only
        )

        # Get unread count
        unread_count = await self.repo.get_unread_count(user_id)

        # Build responses
        notification_responses = [
            NotificationResponse(
                id=n.id,
                user_id=n.user_id,
                type=n.type,
                title=n.title,
                message=n.message,
                related_id=n.related_id,
                image_url=n.image_url,
                is_read=n.is_read,
                created_at=n.created_at
            )
            for n in notifications
        ]

        has_more = (page * page_size) < total

        return NotificationListResponse(
            notifications=notification_responses,
            total=total,
            unread_count=unread_count,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def mark_notification_as_read(
        self,
        notification_id: int,
        user_id: int
    ) -> NotificationMarkReadResponse:
        """Mark a notification as read"""
        # Get notification
        notification = await self.repo.get_notification_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        # Check ownership
        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only mark your own notifications as read"
            )

        # Mark as read
        success = await self.repo.mark_as_read(notification_id)

        return NotificationMarkReadResponse(
            success=success,
            message="Notification marked as read" if success else "Failed to mark notification as read"
        )

    async def mark_all_as_read(self, user_id: int) -> NotificationMarkReadResponse:
        """Mark all user notifications as read"""
        count = await self.repo.mark_all_as_read(user_id)

        return NotificationMarkReadResponse(
            success=True,
            message=f"Marked {count} notifications as read"
        )

    async def delete_notification(
        self,
        notification_id: int,
        user_id: int
    ) -> NotificationDeleteResponse:
        """Delete a notification"""
        # Get notification
        notification = await self.repo.get_notification_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        # Check ownership
        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own notifications"
            )

        # Delete notification
        success = await self.repo.delete_notification(notification_id)

        return NotificationDeleteResponse(
            success=success,
            message="Notification deleted successfully" if success else "Failed to delete notification"
        )

    async def delete_all_notifications(self, user_id: int) -> NotificationDeleteResponse:
        """Delete all user notifications"""
        count = await self.repo.delete_all_notifications(user_id)

        return NotificationDeleteResponse(
            success=True,
            message=f"Deleted {count} notifications"
        )

    async def get_notification_stats(self, user_id: int) -> NotificationStatsResponse:
        """Get notification statistics"""
        stats = await self.repo.get_notification_stats(user_id)

        return NotificationStatsResponse(
            total_count=stats["total_count"],
            unread_count=stats["unread_count"],
            read_count=stats["read_count"]
        )
