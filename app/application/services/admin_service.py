"""Admin business logic service"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.admin_repository import AdminRepository
from app.application.repositories.messaging_repository import MessagingRepository
from app.domain.schemas.admin import (
    MessageReportResponse,
    ReportListResponse,
    ReportOperationResponse,
    GlobalStatsResponse,
    UserStatsResponse,
    UserBasicResponse
)


class AdminService:
    """Service for admin/moderation business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AdminRepository(session)
        self.messaging_repo = MessagingRepository(session)

    async def create_message_report(
        self,
        message_id: int,
        reporter_id: int,
        reason: str
    ) -> ReportOperationResponse:
        """Create a message report"""
        # Check message exists
        message = await self.messaging_repo.get_message_by_id(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Create report
        report = await self.repo.create_message_report(
            message_id=message_id,
            reporter_id=reporter_id,
            reason=reason
        )

        report_response = await self._build_report_response(report)

        return ReportOperationResponse(
            success=True,
            message="Report submitted successfully",
            report=report_response
        )

    async def get_reports(
        self,
        status: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> ReportListResponse:
        """Get all reports with optional status filter"""
        reports, total = await self.repo.get_reports(
            status=status,
            page=page,
            page_size=page_size
        )

        report_responses = []
        for report in reports:
            report_response = await self._build_report_response(report)
            report_responses.append(report_response)

        has_more = (page * page_size) < total

        return ReportListResponse(
            reports=report_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def get_report(self, report_id: int) -> MessageReportResponse:
        """Get a specific report"""
        report = await self.repo.get_report_by_id(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        return await self._build_report_response(report)

    async def resolve_report(
        self,
        report_id: int,
        new_status: str
    ) -> ReportOperationResponse:
        """Resolve a report"""
        # Check report exists
        report = await self.repo.get_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        # Update report
        updated_report = await self.repo.resolve_report(report_id, new_status)

        report_response = await self._build_report_response(updated_report)

        return ReportOperationResponse(
            success=True,
            message=f"Report marked as {new_status}",
            report=report_response
        )

    async def get_global_stats(self) -> GlobalStatsResponse:
        """Get global platform statistics"""
        stats = await self.repo.get_global_stats()

        return GlobalStatsResponse(
            total_users=stats["total_users"],
            total_posts=stats["total_posts"],
            total_channels=stats["total_channels"],
            total_events=stats["total_events"],
            total_messages=stats["total_messages"],
            total_comments=stats["total_comments"],
            total_reports_pending=stats["total_reports_pending"]
        )

    async def get_user_stats(self, user_id: int) -> UserStatsResponse:
        """Get detailed statistics for a user"""
        stats = await self.repo.get_user_stats(user_id)

        return UserStatsResponse(
            user_id=stats["user_id"],
            posts_count=stats["posts_count"],
            comments_count=stats["comments_count"],
            followers_count=stats["followers_count"],
            following_count=stats["following_count"],
            channels_created=stats["channels_created"],
            events_created=stats["events_created"],
            messages_sent=stats["messages_sent"]
        )

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _build_report_response(self, report) -> MessageReportResponse:
        """Build report response with reporter info"""
        reporter = None
        if report.reporter:
            reporter = UserBasicResponse(
                id=report.reporter.id,
                username=report.reporter.username,
                nombre=report.reporter.nombre,
                apellidos=report.reporter.apellidos,
                profile_image_url=report.reporter.profile_image_url
            )

        return MessageReportResponse(
            id=report.id,
            message_id=report.message_id,
            reporter_id=report.reporter_id,
            reason=report.reason,
            status=report.status,
            created_at=report.created_at,
            resolved_at=report.resolved_at,
            reporter=reporter
        )
