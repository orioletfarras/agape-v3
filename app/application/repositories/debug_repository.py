"""Debug repository - Database operations"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import DebugLog


class DebugRepository:
    """Repository for debug log operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(
        self,
        message: str,
        user_id: Optional[int] = None,
        log_level: str = "info",
        context: Optional[str] = None,
        source: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> DebugLog:
        """Create a new debug log entry"""
        log = DebugLog(
            user_id=user_id,
            log_level=log_level,
            message=message,
            context=context,
            source=source,
            device_info=device_info,
            created_at=datetime.utcnow()
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_logs(
        self,
        limit: int = 50,
        user_id: Optional[int] = None,
        log_level: Optional[str] = None
    ) -> List[DebugLog]:
        """Get debug logs with optional filters"""
        query = select(DebugLog).order_by(desc(DebugLog.created_at))

        if user_id:
            query = query.where(DebugLog.user_id == user_id)

        if log_level:
            query = query.where(DebugLog.log_level == log_level)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_logs(self, user_id: Optional[int] = None) -> int:
        """Delete debug logs, optionally filtered by user"""
        if user_id:
            result = await self.session.execute(
                delete(DebugLog).where(DebugLog.user_id == user_id)
            )
        else:
            result = await self.session.execute(delete(DebugLog))

        await self.session.commit()
        return result.rowcount

    async def delete_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            delete(DebugLog).where(DebugLog.created_at < cutoff_date)
        )
        await self.session.commit()
        return result.rowcount
