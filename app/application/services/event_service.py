"""Event business logic service"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.event_repository import EventRepository
from app.application.repositories.channel_repository import ChannelRepository
from app.infrastructure.stripe.stripe_service import StripeService
from app.domain.schemas.event import (
    EventResponse, EventListResponse, EventRegistrationResponse,
    EventRegistrationActionResponse, EventTransactionResponse,
    DiscountCodeResponse, ApplyDiscountResponse, EventAlertResponse,
    EventStatsResponse, EventDeleteResponse, PaymentIntentResponse,
    ChannelBasicResponse, UserBasicResponse
)


class EventService:
    """Service for event business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EventRepository(session)
        self.channel_repo = ChannelRepository(session)
        self.stripe_service = StripeService()

    # ============================================================
    # CRUD OPERATIONS
    # ============================================================

    async def create_event(
        self,
        user_id: int,
        channel_id: int,
        name: str,
        event_date: datetime,
        description: Optional[str] = None,
        end_date: Optional[datetime] = None,
        location: Optional[str] = None,
        image_url: Optional[str] = None,
        max_attendees: Optional[int] = None,
        registration_deadline: Optional[datetime] = None,
        requires_payment: bool = False,
        price: Optional[Decimal] = None,
        currency: str = "EUR"
    ) -> EventResponse:
        """Create a new event (channel admin only)"""
        # Check if user is channel admin
        is_admin = await self.channel_repo.is_user_admin(user_id, channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can create events"
            )

        # Validate payment requirements
        if requires_payment and (not price or price <= 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be specified for paid events"
            )

        # Create event
        event = await self.repo.create_event(
            channel_id=channel_id,
            name=name,
            description=description,
            event_date=event_date,
            end_date=end_date,
            location=location,
            image_url=image_url,
            max_attendees=max_attendees,
            registration_deadline=registration_deadline,
            requires_payment=requires_payment,
            price=price,
            currency=currency
        )

        return await self._build_event_response(event, user_id)

    async def get_event_by_id(self, event_id: int, user_id: int) -> EventResponse:
        """Get a single event by ID"""
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        return await self._build_event_response(event, user_id)

    async def get_events(
        self,
        user_id: int,
        channel_id: Optional[int] = None,
        upcoming_only: bool = True,
        registered_only: bool = False,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> EventListResponse:
        """
        Get events feed for user
        IMPORTANT: Only returns events from channels the user is subscribed to
        """
        events, total = await self.repo.get_events_from_subscribed_channels(
            user_id=user_id,
            channel_id=channel_id,
            upcoming_only=upcoming_only,
            registered_only=registered_only,
            search=search,
            page=page,
            page_size=page_size
        )

        # Build response for each event
        event_responses = []
        for event in events:
            event_response = await self._build_event_response(event, user_id)
            event_responses.append(event_response)

        has_more = (page * page_size) < total

        return EventListResponse(
            events=event_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def update_event(
        self,
        event_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        event_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        location: Optional[str] = None,
        image_url: Optional[str] = None,
        max_attendees: Optional[int] = None,
        registration_deadline: Optional[datetime] = None,
        requires_payment: Optional[bool] = None,
        price: Optional[Decimal] = None,
        currency: Optional[str] = None
    ) -> EventResponse:
        """Update an event (channel admin only)"""
        # Get event
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check if user is channel admin
        is_admin = await self.channel_repo.is_user_admin(user_id, event.channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can update events"
            )

        # Update event
        updated_event = await self.repo.update_event(
            event_id=event_id,
            name=name,
            description=description,
            event_date=event_date,
            end_date=end_date,
            location=location,
            image_url=image_url,
            max_attendees=max_attendees,
            registration_deadline=registration_deadline,
            requires_payment=requires_payment,
            price=price,
            currency=currency
        )

        return await self._build_event_response(updated_event, user_id)

    async def delete_event(self, event_id: int, user_id: int) -> EventDeleteResponse:
        """Delete an event (channel admin only)"""
        # Get event
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check if user is channel admin
        is_admin = await self.channel_repo.is_user_admin(user_id, event.channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can delete events"
            )

        # Delete event
        success = await self.repo.delete_event(event_id)

        return EventDeleteResponse(
            success=success,
            message="Event deleted successfully" if success else "Failed to delete event"
        )

    # ============================================================
    # REGISTRATION OPERATIONS
    # ============================================================

    async def register_for_event(
        self,
        event_id: int,
        user_id: int
    ) -> EventRegistrationActionResponse:
        """Register user for event"""
        # Check if event exists
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check if user can register
        can_register, error_msg = await self.repo.can_register_for_event(event_id)
        if not can_register:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Register user
        registration = await self.repo.register_user_for_event(event_id, user_id)

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already registered for this event"
            )

        # Build response
        registration_response = EventRegistrationResponse(
            id=registration.id,
            event_id=registration.event_id,
            user_id=registration.user_id,
            registered_at=registration.registered_at,
            payment_status=registration.payment_status,
            payment_amount=registration.payment_amount
        )

        message = "Successfully registered for event"
        if event.requires_payment:
            message += ". Please complete payment to confirm your registration."

        return EventRegistrationActionResponse(
            success=True,
            message=message,
            registration=registration_response
        )

    async def cancel_registration(
        self,
        event_id: int,
        user_id: int
    ) -> EventRegistrationActionResponse:
        """Cancel event registration"""
        success = await self.repo.cancel_event_registration(event_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are not registered for this event"
            )

        return EventRegistrationActionResponse(
            success=True,
            message="Registration cancelled successfully",
            registration=None
        )

    async def get_event_registrations(
        self,
        event_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get event registrations (channel admin only)"""
        # Get event
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check if user is channel admin
        is_admin = await self.channel_repo.is_user_admin(user_id, event.channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can view registrations"
            )

        registrations, total = await self.repo.get_event_registrations(
            event_id, page, page_size
        )

        # Build responses
        registration_responses = []
        for reg in registrations:
            user_data = None
            if reg.user:
                user_data = UserBasicResponse(
                    id=reg.user.id,
                    username=reg.user.username,
                    nombre=reg.user.nombre,
                    apellidos=reg.user.apellidos,
                    profile_image_url=reg.user.profile_image_url
                )

            registration_responses.append(
                EventRegistrationResponse(
                    id=reg.id,
                    event_id=reg.event_id,
                    user_id=reg.user_id,
                    registered_at=reg.registered_at,
                    payment_status=reg.payment_status,
                    payment_amount=reg.payment_amount,
                    user=user_data
                )
            )

        has_more = (page * page_size) < total

        return {
            "registrations": registration_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": has_more
        }

    # ============================================================
    # PAYMENT OPERATIONS
    # ============================================================

    async def create_payment_intent(
        self,
        event_id: int,
        user_id: int,
        discount_code: Optional[str] = None
    ) -> PaymentIntentResponse:
        """Create Stripe payment intent for event registration"""
        # Get event
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        if not event.requires_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This event does not require payment"
            )

        # Check if user is registered
        if not await self.repo.is_user_registered(event_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must register for the event first"
            )

        # Calculate amount (with discount if applicable)
        amount = event.price

        if discount_code:
            is_valid, error_msg = await self.repo.validate_discount_code(
                event_id, discount_code
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

            # Apply discount
            discount = await self.repo.get_discount_code(event_id, discount_code)
            if discount.discount_type == "percentage":
                amount = amount * (Decimal("1") - (discount.discount_value / Decimal("100")))
            else:  # fixed
                amount = max(Decimal("0"), amount - discount.discount_value)

            # Mark discount as used
            await self.repo.use_discount_code(event_id, discount_code)

        # Create Stripe payment intent
        payment_intent = await self.stripe_service.create_payment_intent(
            amount=amount,
            currency=event.currency
        )

        if not payment_intent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment intent"
            )

        # Get registration
        registration = await self.repo.get_user_registration(event_id, user_id)

        # Create transaction record
        await self.repo.create_event_transaction(
            event_id=event_id,
            user_id=user_id,
            registration_id=registration.id,
            amount=amount,
            currency=event.currency,
            payment_method="stripe",
            stripe_payment_intent_id=payment_intent["id"]
        )

        return PaymentIntentResponse(
            client_secret=payment_intent["client_secret"],
            amount=amount,
            currency=event.currency
        )

    # ============================================================
    # DISCOUNT CODE OPERATIONS
    # ============================================================

    async def create_discount_code(
        self,
        event_id: int,
        user_id: int,
        code: str,
        discount_type: str,
        discount_value: Decimal,
        max_uses: Optional[int] = None,
        valid_until: Optional[datetime] = None
    ) -> DiscountCodeResponse:
        """Create discount code (channel admin only)"""
        # Get event
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check if user is channel admin
        is_admin = await self.channel_repo.is_user_admin(user_id, event.channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can create discount codes"
            )

        # Create discount code
        discount = await self.repo.create_discount_code(
            event_id=event_id,
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
            valid_until=valid_until
        )

        return DiscountCodeResponse(
            id=discount.id,
            event_id=discount.event_id,
            code=discount.code,
            discount_type=discount.discount_type,
            discount_value=discount.discount_value,
            max_uses=discount.max_uses,
            times_used=discount.times_used,
            valid_until=discount.valid_until,
            created_at=discount.created_at
        )

    async def apply_discount_code(
        self,
        event_id: int,
        code: str
    ) -> ApplyDiscountResponse:
        """Validate and calculate discount"""
        # Get event
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        if not event.requires_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This event does not require payment"
            )

        # Validate discount code
        is_valid, error_msg = await self.repo.validate_discount_code(event_id, code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Calculate discount
        discount = await self.repo.get_discount_code(event_id, code)
        original_price = event.price

        if discount.discount_type == "percentage":
            discount_amount = original_price * (discount.discount_value / Decimal("100"))
        else:  # fixed
            discount_amount = discount.discount_value

        final_price = max(Decimal("0"), original_price - discount_amount)

        return ApplyDiscountResponse(
            success=True,
            message="Discount code applied successfully",
            original_price=original_price,
            discount_amount=discount_amount,
            final_price=final_price
        )

    # ============================================================
    # ALERT OPERATIONS
    # ============================================================

    async def create_event_alert(
        self,
        event_id: int,
        user_id: int,
        title: str,
        message: str
    ) -> EventAlertResponse:
        """Create event alert (channel admin only)"""
        # Get event
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check if user is channel admin
        is_admin = await self.channel_repo.is_user_admin(user_id, event.channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can create alerts"
            )

        alert = await self.repo.create_event_alert(
            event_id=event_id,
            title=title,
            message=message,
            created_by=user_id
        )

        return EventAlertResponse(
            id=alert.id,
            event_id=alert.event_id,
            title=alert.title,
            message=alert.message,
            created_by=alert.created_by,
            created_at=alert.created_at,
            sent_at=alert.sent_at
        )

    async def get_event_alerts(
        self,
        event_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get alerts for an event"""
        alerts, total = await self.repo.get_event_alerts(event_id, page, page_size)

        alert_responses = [
            EventAlertResponse(
                id=alert.id,
                event_id=alert.event_id,
                title=alert.title,
                message=alert.message,
                created_by=alert.created_by,
                created_at=alert.created_at,
                sent_at=alert.sent_at
            )
            for alert in alerts
        ]

        has_more = (page * page_size) < total

        return {
            "alerts": alert_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": has_more
        }

    # ============================================================
    # STATISTICS
    # ============================================================

    async def get_event_stats(
        self,
        event_id: int,
        user_id: int
    ) -> EventStatsResponse:
        """Get event statistics (channel admin only)"""
        # Get event
        event = await self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check if user is channel admin
        is_admin = await self.channel_repo.is_user_admin(user_id, event.channel_id)
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only channel admins can view statistics"
            )

        registered_count = await self.repo.get_registered_count(event_id)
        paid_count = await self.repo.get_paid_count(event_id)
        pending_payment_count = await self.repo.get_pending_payment_count(event_id)
        total_revenue = await self.repo.get_total_revenue(event_id)

        available_spots = None
        if event.max_attendees:
            available_spots = event.max_attendees - registered_count

        return EventStatsResponse(
            registered_count=registered_count,
            paid_count=paid_count,
            pending_payment_count=pending_payment_count,
            total_revenue=total_revenue,
            available_spots=available_spots
        )

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _build_event_response(self, event, user_id: int) -> EventResponse:
        """Build complete event response"""
        # Get counts
        registered_count = await self.repo.get_registered_count(event.id)

        # Get user status
        is_registered = await self.repo.is_user_registered(event.id, user_id)
        has_paid, _ = await self.repo.has_payment_status(event.id, user_id)

        # Build channel response
        channel = None
        if event.channel:
            channel = ChannelBasicResponse(
                id=event.channel.id,
                name=event.channel.name,
                image_url=event.channel.image_url
            )

        return EventResponse(
            id=event.id,
            channel_id=event.channel_id,
            name=event.name,
            description=event.description,
            event_date=event.event_date,
            end_date=event.end_date,
            location=event.location,
            image_url=event.image_url,
            max_attendees=event.max_attendees,
            registration_deadline=event.registration_deadline,
            requires_payment=event.requires_payment,
            price=event.price,
            currency=event.currency,
            created_at=event.created_at,
            updated_at=event.updated_at,
            registered_count=registered_count,
            is_registered=is_registered,
            has_paid=has_paid,
            channel=channel
        )
