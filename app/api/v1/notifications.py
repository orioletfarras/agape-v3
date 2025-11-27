"""Notifications endpoints"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.notification_service import NotificationService
from app.domain.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationStatsResponse,
    NotificationMarkReadResponse,
    NotificationDeleteResponse
)

router = APIRouter(tags=["Notifications"], prefix="/notifications")


# Dependency
async def get_notification_service(session: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(session)


# ============================================================
# GET NOTIFICATIONS ENDPOINTS
# ============================================================

@router.get("", response_model=NotificationListResponse, status_code=status.HTTP_200_OK)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get user's notifications

    Returns paginated list of notifications with option to filter unread only
    """
    return await notification_service.get_user_notifications(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only
    )


@router.get("/stats", response_model=NotificationStatsResponse, status_code=status.HTTP_200_OK)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get notification statistics

    Returns total, unread, and read counts
    """
    return await notification_service.get_notification_stats(current_user.id)


# ============================================================
# MARK AS READ ENDPOINTS
# ============================================================

@router.patch("/{notification_id}/read", response_model=NotificationMarkReadResponse, status_code=status.HTTP_200_OK)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Mark a notification as read

    **Requirements:**
    - Only the notification owner can mark it as read
    """
    return await notification_service.mark_notification_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )


@router.patch("/read-all", response_model=NotificationMarkReadResponse, status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Mark all user notifications as read

    Marks all unread notifications as read for the current user
    """
    return await notification_service.mark_all_as_read(current_user.id)


# ============================================================
# DELETE ENDPOINTS
# ============================================================

@router.delete("/{notification_id}", response_model=NotificationDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Delete a notification

    **Requirements:**
    - Only the notification owner can delete it
    """
    return await notification_service.delete_notification(
        notification_id=notification_id,
        user_id=current_user.id
    )


@router.delete("", response_model=NotificationDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_all_notifications(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Delete all user notifications

    Deletes all notifications for the current user
    """
    return await notification_service.delete_all_notifications(current_user.id)


# ============================================================
# UNREAD COUNT ENDPOINT
# ============================================================

@router.get("/unread/count", response_model=dict, status_code=status.HTTP_200_OK)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get unread notification count

    Returns the count of unread notifications for the current user
    """
    stats = await notification_service.get_notification_stats(current_user.id)
    return {"unread_count": stats.unread_count}
