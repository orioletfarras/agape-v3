"""Events endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.event_service import EventService
from app.infrastructure.aws.s3_service import S3Service
from app.domain.schemas.event import (
    CreateEventRequest,
    UpdateEventRequest,
    RegisterEventRequest,
    ApplyDiscountRequest,
    CreateDiscountCodeRequest,
    CreateEventAlertRequest,
    EventResponse,
    EventListResponse,
    EventRegistrationActionResponse,
    EventDeleteResponse
)

router = APIRouter(tags=["Events"], prefix="/events")


# Dependency
async def get_event_service(session: AsyncSession = Depends(get_db)) -> EventService:
    return EventService(session)


# ============================================================
# EVENT CRUD ENDPOINTS
# ============================================================

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: CreateEventRequest,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Create a new event (channel admin only)"""
    return await event_service.create_event(
        user_id=current_user.id,
        channel_id=data.channel_id,
        name=data.name,
        description=data.description,
        event_date=data.event_date,
        end_date=data.end_date,
        location=data.location,
        image_url=data.image_url,
        max_attendees=data.max_attendees,
        registration_deadline=data.registration_deadline,
        requires_payment=data.requires_payment,
        price=data.price,
        currency=data.currency
    )


@router.get("", response_model=EventListResponse, status_code=status.HTTP_200_OK)
async def get_events(
    channel_id: Optional[int] = Query(None, description="Filter by channel"),
    subscribed_only: bool = Query(True, description="Only show events from subscribed channels"),
    upcoming_only: bool = Query(True, description="Only show upcoming events"),
    registered_only: bool = Query(False, description="Only show events user registered for"),
    search: Optional[str] = Query(None, description="Search in name, description, or location"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """
    Get events feed for authenticated user

    **Filters:**
    - channel_id: Show events from specific channel
    - subscribed_only: Only show events from subscribed channels (default: true)
    - upcoming_only: Only show upcoming events (default: true)
    - registered_only: Only show events user registered for
    - search: Search in event name, description, or location
    - page: Pagination page number
    - page_size: Number of events per page (max 100)
    """
    return await event_service.get_events(
        user_id=current_user.id,
        channel_id=channel_id,
        subscribed_only=subscribed_only,
        upcoming_only=upcoming_only,
        registered_only=registered_only,
        search=search,
        page=page,
        page_size=page_size
    )


@router.get("/{event_id}", response_model=EventResponse, status_code=status.HTTP_200_OK)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Get event by ID"""
    return await event_service.get_event_by_id(event_id, current_user.id)


@router.put("/{event_id}", response_model=EventResponse, status_code=status.HTTP_200_OK)
async def update_event(
    event_id: int,
    data: UpdateEventRequest,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Update event (channel admin only)"""
    return await event_service.update_event(
        event_id=event_id,
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        event_date=data.event_date,
        end_date=data.end_date,
        location=data.location,
        image_url=data.image_url,
        max_attendees=data.max_attendees,
        registration_deadline=data.registration_deadline,
        requires_payment=data.requires_payment,
        price=data.price,
        currency=data.currency
    )


@router.delete("/{event_id}", response_model=EventDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Delete event (channel admin only)"""
    return await event_service.delete_event(event_id, current_user.id)


# ============================================================
# REGISTRATION ENDPOINTS
# ============================================================

@router.post("/{event_id}/register", response_model=EventRegistrationActionResponse, status_code=status.HTTP_200_OK)
async def register_for_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Register for event"""
    return await event_service.register_for_event(event_id, current_user.id)


@router.delete("/{event_id}/register", response_model=EventRegistrationActionResponse, status_code=status.HTTP_200_OK)
async def cancel_registration(
    event_id: int,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Cancel event registration"""
    return await event_service.cancel_registration(event_id, current_user.id)


@router.get("/{event_id}/registrations", status_code=status.HTTP_200_OK)
async def get_event_registrations(
    event_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Get event registrations (channel admin only)"""
    return await event_service.get_event_registrations(
        event_id, current_user.id, page, page_size
    )


# ============================================================
# PAYMENT ENDPOINTS
# ============================================================

@router.post("/{event_id}/payment-intent", status_code=status.HTTP_200_OK)
async def create_payment_intent(
    event_id: int,
    discount_code: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Create Stripe payment intent for event"""
    return await event_service.create_payment_intent(
        event_id, current_user.id, discount_code
    )


# ============================================================
# DISCOUNT CODE ENDPOINTS
# ============================================================

@router.post("/{event_id}/discount-codes", status_code=status.HTTP_201_CREATED)
async def create_discount_code(
    event_id: int,
    data: CreateDiscountCodeRequest,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Create discount code (channel admin only)"""
    return await event_service.create_discount_code(
        event_id=event_id,
        user_id=current_user.id,
        code=data.code,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        max_uses=data.max_uses,
        valid_until=data.valid_until
    )


@router.post("/{event_id}/apply-discount", status_code=status.HTTP_200_OK)
async def apply_discount_code(
    event_id: int,
    data: ApplyDiscountRequest,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Apply discount code and see final price"""
    return await event_service.apply_discount_code(event_id, data.code)


# ============================================================
# ALERT ENDPOINTS
# ============================================================

@router.post("/{event_id}/alerts", status_code=status.HTTP_201_CREATED)
async def create_event_alert(
    event_id: int,
    data: CreateEventAlertRequest,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Create event alert (channel admin only)"""
    return await event_service.create_event_alert(
        event_id=event_id,
        user_id=current_user.id,
        title=data.title,
        message=data.message
    )


@router.get("/{event_id}/alerts", status_code=status.HTTP_200_OK)
async def get_event_alerts(
    event_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Get event alerts"""
    return await event_service.get_event_alerts(event_id, page, page_size)


# ============================================================
# STATISTICS ENDPOINTS
# ============================================================

@router.get("/{event_id}/stats", status_code=status.HTTP_200_OK)
async def get_event_stats(
    event_id: int,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Get event statistics (channel admin only)"""
    return await event_service.get_event_stats(event_id, current_user.id)


# ============================================================
# IMAGE UPLOAD ENDPOINTS
# ============================================================

@router.post("/upload-image", status_code=status.HTTP_200_OK)
async def upload_event_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Upload event image"""
    s3_service = S3Service()

    # Read file data
    file_data = await file.read()

    # Upload to S3
    result = await s3_service.upload_event_image(current_user.id, file_data, file.filename)

    return {
        "success": True,
        "image_url": result["url"]
    }


# ============================================================
# CHANNEL EVENTS ENDPOINT
# ============================================================

@router.get("/channel/{channel_id}", response_model=EventListResponse, status_code=status.HTTP_200_OK)
async def get_channel_events(
    channel_id: int,
    upcoming_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service)
):
    """Get events from specific channel"""
    return await event_service.get_events(
        user_id=current_user.id,
        channel_id=channel_id,
        upcoming_only=upcoming_only,
        page=page,
        page_size=page_size
    )
