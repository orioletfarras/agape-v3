"""Expo Push Notifications Service"""
import logging
from typing import List, Dict, Any, Optional
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


class ExpoPushService:
    """Service for sending push notifications via Expo"""

    def __init__(self):
        self.access_token = settings.EXPO_ACCESS_TOKEN

    async def send_push_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        sound: str = "default",
        badge: Optional[int] = None,
        priority: str = "default",
    ) -> bool:
        """
        Send a push notification to a single device

        Args:
            token: Expo push token
            title: Notification title
            body: Notification body
            data: Additional data payload
            sound: Notification sound
            badge: Badge count
            priority: "default", "normal", or "high"

        Returns:
            bool: True if sent successfully
        """
        try:
            # Validate token format
            if not PushClient.is_exponent_push_token(token):
                logger.error(f"Invalid Expo push token: {token}")
                return False

            # Create message
            message = PushMessage(
                to=token,
                title=title,
                body=body,
                data=data or {},
                sound=sound,
                badge=badge,
                priority=priority,
            )

            # Send notification
            response = PushClient().publish(message)

            # Check for errors
            if response.is_success():
                logger.info(f"Push notification sent successfully to {token}")
                return True
            else:
                logger.error(f"Failed to send push notification: {response.message}")
                return False

        except DeviceNotRegisteredError:
            logger.warning(f"Device not registered: {token}")
            return False
        except PushServerError as e:
            logger.error(f"Expo push server error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False

    async def send_push_notifications_batch(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        sound: str = "default",
        badge: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Send push notifications to multiple devices

        Args:
            tokens: List of Expo push tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            sound: Notification sound
            badge: Badge count

        Returns:
            dict: Statistics {success: int, failed: int}
        """
        stats = {"success": 0, "failed": 0}

        try:
            # Filter valid tokens
            valid_tokens = [token for token in tokens if PushClient.is_exponent_push_token(token)]

            if not valid_tokens:
                logger.warning("No valid Expo push tokens provided")
                return stats

            # Create messages
            messages = [
                PushMessage(
                    to=token,
                    title=title,
                    body=body,
                    data=data or {},
                    sound=sound,
                    badge=badge,
                )
                for token in valid_tokens
            ]

            # Send in batches (Expo recommends batches of 100)
            batch_size = 100
            for i in range(0, len(messages), batch_size):
                batch = messages[i : i + batch_size]

                try:
                    responses = PushClient().publish_multiple(batch)

                    # Count successes and failures
                    for response in responses:
                        if response.is_success():
                            stats["success"] += 1
                        else:
                            stats["failed"] += 1
                            logger.error(f"Failed to send notification: {response.message}")

                except PushServerError as e:
                    logger.error(f"Batch push failed: {e}")
                    stats["failed"] += len(batch)

            logger.info(f"Batch push completed: {stats['success']} success, {stats['failed']} failed")
            return stats

        except Exception as e:
            logger.error(f"Error sending batch push notifications: {e}")
            return stats

    async def send_notification_to_user(
        self,
        user_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send notification to all devices of a user

        Args:
            user_tokens: List of user's push tokens
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            bool: True if at least one notification was sent
        """
        if not user_tokens:
            return False

        stats = await self.send_push_notifications_batch(
            tokens=user_tokens,
            title=title,
            body=body,
            data=data,
        )

        return stats["success"] > 0

    async def send_channel_alert(
        self,
        tokens: List[str],
        channel_name: str,
        message: str,
    ) -> Dict[str, int]:
        """Send alert from a channel to subscribers"""
        return await self.send_push_notifications_batch(
            tokens=tokens,
            title=f"Alerta de {channel_name}",
            body=message,
            data={"type": "channel_alert", "channel_name": channel_name},
        )

    async def send_event_alert(
        self,
        tokens: List[str],
        event_title: str,
        message: str,
        event_id: int,
    ) -> Dict[str, int]:
        """Send event alert to attendees"""
        return await self.send_push_notifications_batch(
            tokens=tokens,
            title=f"Evento: {event_title}",
            body=message,
            data={"type": "event_alert", "event_id": event_id},
        )

    async def send_new_post_notification(
        self,
        tokens: List[str],
        channel_name: str,
        post_preview: str,
        post_id: int,
    ) -> Dict[str, int]:
        """Send notification for new post in subscribed channel"""
        return await self.send_push_notifications_batch(
            tokens=tokens,
            title=f"Nueva publicación en {channel_name}",
            body=post_preview[:100],
            data={"type": "new_post", "post_id": post_id},
        )

    async def send_comment_notification(
        self,
        tokens: List[str],
        commenter_name: str,
        comment_preview: str,
        post_id: int,
    ) -> Dict[str, int]:
        """Send notification for new comment"""
        return await self.send_push_notifications_batch(
            tokens=tokens,
            title=f"{commenter_name} comentó tu publicación",
            body=comment_preview[:100],
            data={"type": "comment", "post_id": post_id},
        )

    async def send_like_notification(
        self,
        tokens: List[str],
        liker_name: str,
        post_id: int,
    ) -> Dict[str, int]:
        """Send notification for post like"""
        return await self.send_push_notifications_batch(
            tokens=tokens,
            title="Nueva reacción",
            body=f"A {liker_name} le gustó tu publicación",
            data={"type": "like", "post_id": post_id},
            sound="default",
            badge=1,
        )


# Singleton instance
expo_push_service = ExpoPushService()
