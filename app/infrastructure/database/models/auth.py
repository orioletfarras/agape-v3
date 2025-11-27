from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class RefreshToken(Base):
    """Refresh tokens for JWT authentication"""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Token
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Device info
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)  # ios, android, web

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_token", "token"),
        Index("idx_refresh_user_expires", "user_id", "expires_at"),
    )

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"


class OTPCode(Base):
    """OTP codes for email/SMS verification"""

    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User identification (email or phone)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)

    # OTP details
    code = Column(String(10), nullable=False)
    method = Column(String(20), nullable=False)  # email, sms
    purpose = Column(String(50), nullable=False)  # login, register, password_reset

    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)

    # Expiry
    expires_at = Column(DateTime, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_otp_email_expires", "email", "expires_at"),
        Index("idx_otp_phone_expires", "phone", "expires_at"),
    )

    def __repr__(self):
        return f"<OTPCode(id={self.id}, email={self.email}, purpose={self.purpose})>"


class RegistrationSession(Base):
    """Temporary registration sessions"""

    __tablename__ = "registration_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    registration_id = Column(String(100), unique=True, nullable=False, index=True)

    # User data
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Verification
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)

    # Status
    is_completed = Column(Boolean, default=False, nullable=False)
    is_expired = Column(Boolean, default=False, nullable=False)

    # Expiry
    expires_at = Column(DateTime, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_reg_session_id", "registration_id"),
        Index("idx_reg_email_expires", "email", "expires_at"),
    )

    def __repr__(self):
        return f"<RegistrationSession(id={self.id}, registration_id={self.registration_id})>"


class VerificationSession(Base):
    """Identity verification sessions (for KYC, etc)"""

    __tablename__ = "verification_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Status
    status = Column(String(50), default="pending", nullable=False)  # pending, verified, failed
    verification_url = Column(String(500), nullable=True)

    # Results
    verified_at = Column(DateTime, nullable=True)
    failed_reason = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("idx_verification_session_id", "session_id"),
        Index("idx_verification_user", "user_id"),
    )

    def __repr__(self):
        return f"<VerificationSession(id={self.id}, session_id={self.session_id}, status={self.status})>"
