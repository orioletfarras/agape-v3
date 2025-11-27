"""Debug service - Business logic"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.debug_repository import DebugRepository
from app.domain.schemas.debug import (
    SaveLogsRequest,
    GetLogsResponse,
    DeleteLogsResponse,
    DebugLogResponse
)


class DebugService:
    """Service for debug operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DebugRepository(session)

    async def save_logs(
        self,
        request: SaveLogsRequest,
        user_id: Optional[int] = None
    ) -> dict:
        """Save multiple log entries from client"""
        saved_count = 0

        for log_message in request.logs:
            await self.repo.create_log(
                message=log_message,
                user_id=user_id,
                log_level=request.log_level or "info",
                context=request.context,
                source=request.source or "mobile",
                device_info=request.device_info
            )
            saved_count += 1

        return {
            "success": True,
            "saved_count": saved_count
        }

    async def get_logs(
        self,
        limit: int = 50,
        user_id: Optional[int] = None
    ) -> GetLogsResponse:
        """Get debug logs"""
        logs = await self.repo.get_logs(limit=limit, user_id=user_id)

        # Convert to simple log messages
        log_messages = [
            f"[{log.created_at.isoformat()}] [{log.log_level.upper()}] {log.message}"
            for log in logs
        ]

        return GetLogsResponse(
            logs=log_messages,
            total=len(log_messages)
        )

    async def delete_logs(self, user_id: Optional[int] = None) -> DeleteLogsResponse:
        """Delete debug logs"""
        deleted_count = await self.repo.delete_logs(user_id=user_id)

        return DeleteLogsResponse(
            success=True,
            deleted_count=deleted_count,
            message=f"Deleted {deleted_count} log entries"
        )
