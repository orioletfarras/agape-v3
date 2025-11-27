"""Donation models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Donation(Base):
    """User donations to channels"""
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)

    # Donation details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    hide_amount = Column(Boolean, default=False, nullable=False)

    # Stripe details
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, unique=True, index=True)

    # Status
    status = Column(String(50), default="active", nullable=False)  # active, cancelled, paused
    payment_status = Column(String(50), default="pending", nullable=False)  # pending, paid, failed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="donations")
    channel = relationship("Channel", back_populates="donations")

    __table_args__ = (
        Index("idx_donation_user_channel", "user_id", "channel_id"),
        Index("idx_donation_stripe_sub", "stripe_subscription_id"),
    )


class DonationCertificate(Base):
    """Donation certificates for tax purposes"""
    __tablename__ = "donation_certificates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Certificate details
    year = Column(Integer, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    certificate_url = Column(String(500), nullable=True)
    certificate_number = Column(String(100), unique=True, nullable=False, index=True)

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="donation_certificates")

    __table_args__ = (
        Index("idx_certificate_user_year", "user_id", "year", unique=True),
    )
