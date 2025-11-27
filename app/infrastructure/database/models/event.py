from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Event(Base):
    """Event model - Eventos del calendario"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Basic info
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Dates
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=True)

    # Location
    location = Column(String(500), nullable=True)

    # Pricing
    event_price = Column(Numeric(10, 2), nullable=True)
    allow_installments = Column(Boolean, default=False, nullable=False)
    reservation_amount = Column(Numeric(10, 2), nullable=True)
    payment_deadline = Column(String(50), nullable=True)  # DD/MM/YYYY format

    # Capacity
    goal_attendees = Column(Integer, nullable=True)

    # Media
    image_url = Column(String(500), nullable=True)

    # Relations
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    channel = relationship("Channel", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")
    discount_codes = relationship("DiscountCode", back_populates="event", cascade="all, delete-orphan")
    alerts = relationship("EventAlert", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_event_channel_date", "channel_id", "start_date"),
        Index("idx_event_dates", "start_date", "end_date"),
    )

    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title})>"


class EventRegistration(Base):
    """Event registrations and tickets"""

    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Relations
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Ticket info
    ticket_code = Column(String(100), unique=True, nullable=False, index=True)
    checked_in = Column(Boolean, default=False, nullable=False)
    check_in_time = Column(DateTime, nullable=True)
    ticket_used = Column(Boolean, default=False, nullable=False)

    # Payment info
    payment_status = Column(String(50), default="pending", nullable=False)  # pending, completed, failed
    total_price = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0, nullable=False)
    amount_pending = Column(Numeric(10, 2), nullable=True)

    # Installment info
    payment_option = Column(String(50), nullable=False)  # full, installments, free
    installments = Column(Integer, nullable=True)
    installment_amount = Column(Numeric(10, 2), nullable=True)

    # Stripe
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)

    # Attendee info
    total_attendees = Column(Integer, default=1, nullable=False)
    include_user = Column(Boolean, default=True, nullable=False)

    # Timestamps
    registration_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    purchase_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="registrations")
    user = relationship("User", back_populates="event_registrations")
    transactions = relationship("EventTransaction", back_populates="registration", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_event_reg_ticket", "ticket_code"),
        Index("idx_event_reg_user", "user_id", "event_id"),
    )

    def __repr__(self):
        return f"<EventRegistration(id={self.id}, event_id={self.event_id}, ticket={self.ticket_code})>"


class EventTransaction(Base):
    """Individual payment transactions for event registrations"""

    __tablename__ = "event_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Relations
    registration_id = Column(Integer, ForeignKey("event_registrations.id"), nullable=False, index=True)

    # Transaction info
    installment_number = Column(Integer, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False)  # pending, completed, failed, refunded

    # Stripe
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)
    stripe_refund_id = Column(String(255), nullable=True)

    # Refund
    refund_amount = Column(Numeric(10, 2), nullable=True)
    refund_date = Column(DateTime, nullable=True)

    # Timestamps
    payment_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    registration = relationship("EventRegistration", back_populates="transactions")

    __table_args__ = (
        Index("idx_transaction_registration", "registration_id"),
        Index("idx_transaction_stripe", "stripe_payment_intent_id"),
    )

    def __repr__(self):
        return f"<EventTransaction(id={self.id}, registration_id={self.registration_id}, amount={self.amount})>"


class DiscountCode(Base):
    """Discount codes for events"""

    __tablename__ = "discount_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Relations
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)

    # Code info
    code = Column(String(100), nullable=False, index=True)
    discount_type = Column(String(20), nullable=False)  # percentage, fixed
    discount_value = Column(Numeric(10, 2), nullable=False)

    # Validity
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    times_used = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Stats
    total_discount_amount = Column(Numeric(10, 2), default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="discount_codes")

    __table_args__ = (
        Index("idx_discount_event_code", "event_id", "code", unique=True),
    )

    def __repr__(self):
        return f"<DiscountCode(id={self.id}, code={self.code})>"


class EventAlert(Base):
    """Alerts sent to event attendees"""

    __tablename__ = "event_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="alerts")

    __table_args__ = (
        Index("idx_event_alert_created", "event_id", "created_at"),
    )

    def __repr__(self):
        return f"<EventAlert(id={self.id}, event_id={self.event_id})>"
