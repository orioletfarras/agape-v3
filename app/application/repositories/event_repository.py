"""Event repository for database operations"""
from typing import List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    Event, EventRegistration, EventTransaction, DiscountCode,
    EventAlert, Channel, User, ChannelSubscription
)


class EventRepository:
    """Repository for event-related database operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # CRUD OPERATIONS
    # ============================================================

    async def create_event(
        self,
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
    ) -> Event:
        """Create a new event"""
        event = Event(
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
            currency=currency,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Get event by ID with related data"""
        result = await self.session.execute(
            select(Event)
            .options(selectinload(Event.channel))
            .where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_events_from_subscribed_channels(
        self,
        user_id: int,
        channel_id: Optional[int] = None,
        upcoming_only: bool = True,
        registered_only: bool = False,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Event], int]:
        """
        Get events from channels user is subscribed to
        Returns (events, total_count)
        """
        # Base query: events from subscribed channels
        query = (
            select(Event)
            .join(ChannelSubscription, ChannelSubscription.channel_id == Event.channel_id)
            .where(ChannelSubscription.user_id == user_id)
            .options(selectinload(Event.channel))
        )

        # Filter by channel
        if channel_id:
            query = query.where(Event.channel_id == channel_id)

        # Filter upcoming events only
        if upcoming_only:
            query = query.where(Event.event_date >= datetime.utcnow())

        # Filter registered events only
        if registered_only:
            query = query.join(
                EventRegistration,
                EventRegistration.event_id == Event.id
            ).where(EventRegistration.user_id == user_id)

        # Search by name, description, or location
        if search:
            query = query.where(
                or_(
                    Event.name.ilike(f"%{search}%"),
                    Event.description.ilike(f"%{search}%"),
                    Event.location.ilike(f"%{search}%")
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Event.event_date.asc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.session.execute(query)
        events = result.scalars().all()

        return list(events), total

    async def update_event(
        self,
        event_id: int,
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
    ) -> Optional[Event]:
        """Update an event"""
        event = await self.get_event_by_id(event_id)
        if not event:
            return None

        if name is not None:
            event.name = name
        if description is not None:
            event.description = description
        if event_date is not None:
            event.event_date = event_date
        if end_date is not None:
            event.end_date = end_date
        if location is not None:
            event.location = location
        if image_url is not None:
            event.image_url = image_url
        if max_attendees is not None:
            event.max_attendees = max_attendees
        if registration_deadline is not None:
            event.registration_deadline = registration_deadline
        if requires_payment is not None:
            event.requires_payment = requires_payment
        if price is not None:
            event.price = price
        if currency is not None:
            event.currency = currency

        event.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def delete_event(self, event_id: int) -> bool:
        """Delete an event"""
        event = await self.get_event_by_id(event_id)
        if not event:
            return False

        await self.session.delete(event)
        await self.session.commit()
        return True

    # ============================================================
    # REGISTRATION OPERATIONS
    # ============================================================

    async def register_user_for_event(
        self,
        event_id: int,
        user_id: int
    ) -> Optional[EventRegistration]:
        """Register user for event"""
        # Check if already registered
        existing = await self.session.execute(
            select(EventRegistration).where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.user_id == user_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return None

        registration = EventRegistration(
            event_id=event_id,
            user_id=user_id,
            registered_at=datetime.utcnow(),
            payment_status="pending" if await self._event_requires_payment(event_id) else "not_required"
        )
        self.session.add(registration)
        await self.session.commit()
        await self.session.refresh(registration)
        return registration

    async def cancel_event_registration(self, event_id: int, user_id: int) -> bool:
        """Cancel event registration"""
        result = await self.session.execute(
            delete(EventRegistration).where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.user_id == user_id
                )
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def is_user_registered(self, event_id: int, user_id: int) -> bool:
        """Check if user is registered for event"""
        result = await self.session.execute(
            select(EventRegistration).where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_user_registration(
        self,
        event_id: int,
        user_id: int
    ) -> Optional[EventRegistration]:
        """Get user's registration for event"""
        result = await self.session.execute(
            select(EventRegistration)
            .options(selectinload(EventRegistration.user))
            .where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_event_registrations(
        self,
        event_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[EventRegistration], int]:
        """Get all registrations for an event"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(EventRegistration.id))
            .where(EventRegistration.event_id == event_id)
        )
        total = count_result.scalar() or 0

        # Get registrations with user info
        query = (
            select(EventRegistration)
            .options(selectinload(EventRegistration.user))
            .where(EventRegistration.event_id == event_id)
            .order_by(EventRegistration.registered_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        registrations = result.scalars().all()

        return list(registrations), total

    # ============================================================
    # PAYMENT OPERATIONS
    # ============================================================

    async def create_event_transaction(
        self,
        event_id: int,
        user_id: int,
        registration_id: int,
        amount: Decimal,
        currency: str,
        payment_method: str,
        stripe_payment_intent_id: Optional[str] = None
    ) -> EventTransaction:
        """Create event payment transaction"""
        transaction = EventTransaction(
            event_id=event_id,
            user_id=user_id,
            registration_id=registration_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            stripe_payment_intent_id=stripe_payment_intent_id,
            status="pending",
            created_at=datetime.utcnow()
        )
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def update_transaction_status(
        self,
        transaction_id: int,
        status: str
    ) -> Optional[EventTransaction]:
        """Update transaction status"""
        result = await self.session.execute(
            select(EventTransaction).where(EventTransaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            return None

        transaction.status = status
        await self.session.commit()
        await self.session.refresh(transaction)

        # Update registration payment status
        if status == "completed":
            registration_result = await self.session.execute(
                select(EventRegistration).where(
                    EventRegistration.id == transaction.registration_id
                )
            )
            registration = registration_result.scalar_one_or_none()
            if registration:
                registration.payment_status = "paid"
                registration.payment_amount = transaction.amount
                await self.session.commit()

        return transaction

    # ============================================================
    # DISCOUNT CODE OPERATIONS
    # ============================================================

    async def create_discount_code(
        self,
        event_id: int,
        code: str,
        discount_type: str,
        discount_value: Decimal,
        max_uses: Optional[int] = None,
        valid_until: Optional[datetime] = None
    ) -> DiscountCode:
        """Create discount code"""
        discount = DiscountCode(
            event_id=event_id,
            code=code.upper(),
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
            times_used=0,
            valid_until=valid_until,
            created_at=datetime.utcnow()
        )
        self.session.add(discount)
        await self.session.commit()
        await self.session.refresh(discount)
        return discount

    async def get_discount_code(self, event_id: int, code: str) -> Optional[DiscountCode]:
        """Get discount code"""
        result = await self.session.execute(
            select(DiscountCode).where(
                and_(
                    DiscountCode.event_id == event_id,
                    DiscountCode.code == code.upper()
                )
            )
        )
        return result.scalar_one_or_none()

    async def validate_discount_code(
        self,
        event_id: int,
        code: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate discount code and return (is_valid, error_message)"""
        discount = await self.get_discount_code(event_id, code)

        if not discount:
            return False, "Invalid discount code"

        if discount.max_uses and discount.times_used >= discount.max_uses:
            return False, "Discount code has reached maximum uses"

        if discount.valid_until and discount.valid_until < datetime.utcnow():
            return False, "Discount code has expired"

        return True, None

    async def use_discount_code(self, event_id: int, code: str) -> bool:
        """Increment discount code usage"""
        discount = await self.get_discount_code(event_id, code)
        if not discount:
            return False

        discount.times_used += 1
        await self.session.commit()
        return True

    # ============================================================
    # ALERT OPERATIONS
    # ============================================================

    async def create_event_alert(
        self,
        event_id: int,
        title: str,
        message: str,
        created_by: int
    ) -> EventAlert:
        """Create event alert"""
        alert = EventAlert(
            event_id=event_id,
            title=title,
            message=message,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_event_alerts(
        self,
        event_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[EventAlert], int]:
        """Get alerts for an event"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(EventAlert.id))
            .where(EventAlert.event_id == event_id)
        )
        total = count_result.scalar() or 0

        # Get alerts
        query = (
            select(EventAlert)
            .where(EventAlert.event_id == event_id)
            .order_by(EventAlert.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        alerts = result.scalars().all()

        return list(alerts), total

    # ============================================================
    # STATISTICS
    # ============================================================

    async def get_registered_count(self, event_id: int) -> int:
        """Get number of registered users"""
        result = await self.session.execute(
            select(func.count(EventRegistration.id))
            .where(EventRegistration.event_id == event_id)
        )
        return result.scalar() or 0

    async def get_paid_count(self, event_id: int) -> int:
        """Get number of users who paid"""
        result = await self.session.execute(
            select(func.count(EventRegistration.id))
            .where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.payment_status == "paid"
                )
            )
        )
        return result.scalar() or 0

    async def get_pending_payment_count(self, event_id: int) -> int:
        """Get number of users with pending payment"""
        result = await self.session.execute(
            select(func.count(EventRegistration.id))
            .where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.payment_status == "pending"
                )
            )
        )
        return result.scalar() or 0

    async def get_total_revenue(self, event_id: int) -> Decimal:
        """Get total revenue from event"""
        result = await self.session.execute(
            select(func.sum(EventTransaction.amount))
            .where(
                and_(
                    EventTransaction.event_id == event_id,
                    EventTransaction.status == "completed"
                )
            )
        )
        total = result.scalar()
        return Decimal(str(total)) if total else Decimal("0")

    async def has_payment_status(
        self,
        event_id: int,
        user_id: int
    ) -> Tuple[bool, str]:
        """Check user payment status. Returns (has_paid, status)"""
        result = await self.session.execute(
            select(EventRegistration).where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.user_id == user_id
                )
            )
        )
        registration = result.scalar_one_or_none()

        if not registration:
            return False, "not_registered"

        return registration.payment_status == "paid", registration.payment_status

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _event_requires_payment(self, event_id: int) -> bool:
        """Check if event requires payment"""
        event = await self.get_event_by_id(event_id)
        return event.requires_payment if event else False

    async def can_register_for_event(self, event_id: int) -> Tuple[bool, Optional[str]]:
        """Check if event is open for registration"""
        event = await self.get_event_by_id(event_id)

        if not event:
            return False, "Event not found"

        # Check registration deadline
        if event.registration_deadline and event.registration_deadline < datetime.utcnow():
            return False, "Registration deadline has passed"

        # Check max attendees
        if event.max_attendees:
            registered_count = await self.get_registered_count(event_id)
            if registered_count >= event.max_attendees:
                return False, "Event is full"

        return True, None
