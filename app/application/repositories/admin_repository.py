"""Admin repository - Database operations"""
from typing import Tuple, List, Optional
from datetime import datetime
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    MessageReport, User, Post, Channel, Event, Message, Comment, Follow
)


class AdminRepository:
    """Repository for admin/moderation operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # REPORT OPERATIONS
    # ============================================================

    async def create_message_report(
        self,
        message_id: int,
        reporter_id: int,
        reason: str
    ) -> MessageReport:
        """Create a message report"""
        report = MessageReport(
            message_id=message_id,
            reporter_id=reporter_id,
            reason=reason,
            status="pending",
            created_at=datetime.utcnow()
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_report_by_id(self, report_id: int) -> Optional[MessageReport]:
        """Get report by ID"""
        result = await self.session.execute(
            select(MessageReport)
            .options(selectinload(MessageReport.reporter))
            .where(MessageReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def get_reports(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[MessageReport], int]:
        """Get all reports with optional status filter"""
        query = select(MessageReport).options(selectinload(MessageReport.reporter))

        if status:
            query = query.where(MessageReport.status == status)

        # Count total
        count_query = select(func.count(MessageReport.id))
        if status:
            count_query = count_query.where(MessageReport.status == status)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get reports
        query = (
            query
            .order_by(MessageReport.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        reports = result.scalars().all()

        return list(reports), total

    async def resolve_report(
        self,
        report_id: int,
        status: str
    ) -> Optional[MessageReport]:
        """Resolve a report"""
        await self.session.execute(
            update(MessageReport)
            .where(MessageReport.id == report_id)
            .values(
                status=status,
                resolved_at=datetime.utcnow()
            )
        )
        await self.session.commit()

        return await self.get_report_by_id(report_id)

    # ============================================================
    # STATISTICS OPERATIONS
    # ============================================================

    async def get_global_stats(self) -> dict:
        """Get global platform statistics"""
        # Total users
        users_result = await self.session.execute(select(func.count(User.id)))
        total_users = users_result.scalar() or 0

        # Total posts
        posts_result = await self.session.execute(select(func.count(Post.id)))
        total_posts = posts_result.scalar() or 0

        # Total channels
        channels_result = await self.session.execute(select(func.count(Channel.id)))
        total_channels = channels_result.scalar() or 0

        # Total events
        events_result = await self.session.execute(select(func.count(Event.id)))
        total_events = events_result.scalar() or 0

        # Total messages
        messages_result = await self.session.execute(select(func.count(Message.id)))
        total_messages = messages_result.scalar() or 0

        # Total comments
        comments_result = await self.session.execute(select(func.count(Comment.id)))
        total_comments = comments_result.scalar() or 0

        # Pending reports
        reports_result = await self.session.execute(
            select(func.count(MessageReport.id))
            .where(MessageReport.status == "pending")
        )
        total_reports_pending = reports_result.scalar() or 0

        return {
            "total_users": total_users,
            "total_posts": total_posts,
            "total_channels": total_channels,
            "total_events": total_events,
            "total_messages": total_messages,
            "total_comments": total_comments,
            "total_reports_pending": total_reports_pending
        }

    async def get_user_stats(self, user_id: int) -> dict:
        """Get detailed statistics for a user"""
        # Posts count
        posts_result = await self.session.execute(
            select(func.count(Post.id))
            .where(Post.author_id == user_id)
        )
        posts_count = posts_result.scalar() or 0

        # Comments count
        comments_result = await self.session.execute(
            select(func.count(Comment.id))
            .where(Comment.author_id == user_id)
        )
        comments_count = comments_result.scalar() or 0

        # Followers count
        followers_result = await self.session.execute(
            select(func.count(Follow.id))
            .where(Follow.followed_id == user_id)
        )
        followers_count = followers_result.scalar() or 0

        # Following count
        following_result = await self.session.execute(
            select(func.count(Follow.id))
            .where(Follow.follower_id == user_id)
        )
        following_count = following_result.scalar() or 0

        # Channels created
        channels_result = await self.session.execute(
            select(func.count(Channel.id))
            .where(Channel.created_by == user_id)
        )
        channels_created = channels_result.scalar() or 0

        # Events created
        events_result = await self.session.execute(
            select(func.count(Event.id))
            .where(Event.created_by == user_id)
        )
        events_created = events_result.scalar() or 0

        # Messages sent
        messages_result = await self.session.execute(
            select(func.count(Message.id))
            .where(Message.sender_id == user_id)
        )
        messages_sent = messages_result.scalar() or 0

        return {
            "user_id": user_id,
            "posts_count": posts_count,
            "comments_count": comments_count,
            "followers_count": followers_count,
            "following_count": following_count,
            "channels_created": channels_created,
            "events_created": events_created,
            "messages_sent": messages_sent
        }
