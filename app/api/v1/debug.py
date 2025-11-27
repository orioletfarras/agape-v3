"""Debug endpoints - Client logging and debugging"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user_optional
from app.application.services.debug_service import DebugService
from app.domain.schemas.debug import (
    SaveLogsRequest,
    GetLogsResponse,
    DeleteLogsResponse
)

router = APIRouter(tags=["Debug"], prefix="/debug")


# Dependency
async def get_debug_service(session: AsyncSession = Depends(get_db)) -> DebugService:
    return DebugService(session)


@router.post("/logs", status_code=status.HTTP_200_OK)
async def save_debug_logs(
    request: SaveLogsRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    debug_service: DebugService = Depends(get_debug_service)
):
    """
    Save debug logs from client

    **Request body:**
    ```json
    {
      "logs": ["string"],
      "log_level": "info | warning | error | debug",
      "source": "mobile | web",
      "context": "JSON string with additional context",
      "device_info": "JSON string with device information"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "saved_count": 5
    }
    ```
    """
    user_id = current_user.id if current_user else None
    return await debug_service.save_logs(request, user_id=user_id)


@router.get("/logs", response_model=GetLogsResponse, status_code=status.HTTP_200_OK)
async def get_debug_logs(
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of logs to return"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    debug_service: DebugService = Depends(get_debug_service)
):
    """
    Get debug logs

    **Query params:**
    - `limit`: Maximum number of logs (default: 50, max: 1000)

    **Response:**
    ```json
    {
      "logs": ["[2025-01-15T10:30:00] [INFO] Log message"],
      "total": 50
    }
    ```
    """
    user_id = current_user.id if current_user else None
    return await debug_service.get_logs(limit=limit, user_id=user_id)


@router.delete("/logs", response_model=DeleteLogsResponse, status_code=status.HTTP_200_OK)
async def delete_debug_logs(
    current_user: Optional[User] = Depends(get_current_user_optional),
    debug_service: DebugService = Depends(get_debug_service)
):
    """
    Delete all debug logs

    **Response:**
    ```json
    {
      "success": true,
      "deleted_count": 123,
      "message": "Deleted 123 log entries"
    }
    ```
    """
    user_id = current_user.id if current_user else None
    return await debug_service.delete_logs(user_id=user_id)
