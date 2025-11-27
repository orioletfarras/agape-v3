"""Admin and Moderation endpoints"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.admin_service import AdminService
from app.domain.schemas.admin import (
    CreateMessageReportRequest,
    ResolveReportRequest,
    MessageReportResponse,
    ReportListResponse,
    ReportOperationResponse,
    GlobalStatsResponse,
    UserStatsResponse
)

router = APIRouter(tags=["Admin"], prefix="/admin")


# Dependency
async def get_admin_service(session: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(session)


# ============================================================
# REPORT ENDPOINTS
# ============================================================

@router.post("/reports", response_model=ReportOperationResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    data: CreateMessageReportRequest,
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Report a message

    **Requirements:**
    - Must be authenticated
    - Message must exist
    """
    return await admin_service.create_message_report(
        message_id=data.message_id,
        reporter_id=current_user.id,
        reason=data.reason
    )


@router.get("/reports", response_model=ReportListResponse, status_code=status.HTTP_200_OK)
async def get_reports(
    status_filter: str = Query(None, alias="status", pattern="^(pending|reviewed|resolved)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get all reports with optional status filter

    **Query Parameters:**
    - `status` (optional): Filter by status (pending, reviewed, resolved)
    - `page` (optional): Page number
    - `page_size` (optional): Items per page

    **Note:** In a production app, this should be restricted to admin users only
    """
    return await admin_service.get_reports(
        status=status_filter,
        page=page,
        page_size=page_size
    )


@router.get("/reports/{report_id}", response_model=MessageReportResponse, status_code=status.HTTP_200_OK)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get a specific report by ID

    **Note:** In a production app, this should be restricted to admin users only
    """
    return await admin_service.get_report(report_id)


@router.patch("/reports/{report_id}/resolve", response_model=ReportOperationResponse, status_code=status.HTTP_200_OK)
async def resolve_report(
    report_id: int,
    data: ResolveReportRequest,
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Resolve a report

    **Requirements:**
    - Status must be "reviewed" or "resolved"

    **Note:** In a production app, this should be restricted to admin users only
    """
    return await admin_service.resolve_report(
        report_id=report_id,
        new_status=data.status
    )


# ============================================================
# STATISTICS ENDPOINTS
# ============================================================

@router.get("/stats/global", response_model=GlobalStatsResponse, status_code=status.HTTP_200_OK)
async def get_global_stats(
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get global platform statistics

    Returns counts for:
    - Total users
    - Total posts
    - Total channels
    - Total events
    - Total messages
    - Total comments
    - Pending reports

    **Note:** In a production app, this should be restricted to admin users only
    """
    return await admin_service.get_global_stats()


@router.get("/stats/users/{user_id}", response_model=UserStatsResponse, status_code=status.HTTP_200_OK)
async def get_user_stats(
    user_id: int,
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get detailed statistics for a specific user

    Returns:
    - Posts count
    - Comments count
    - Followers/following count
    - Channels created
    - Events created
    - Messages sent

    **Note:** In a production app, this should be restricted to admin users or the user themselves
    """
    return await admin_service.get_user_stats(user_id)
