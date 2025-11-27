from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Notification(Base):
    """Notifications model"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Type
    type = Column(String(100), nullable=False, index=True)
    # Types: spouse_request, channel_invite, friend_request, follow_request,
    # event_invite, event_alert, children_sharing_request, system_notification

    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional data

    # Relations
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Status
    status = Column(String(50), default="pending", nullable=False)  # pending, accepted, rejected
    is_read = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    sender = relationship("User", back_populates="notifications_sent", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="notifications_received", foreign_keys=[receiver_id])

    __table_args__ = (
        Index("idx_notif_receiver_created", "receiver_id", "created_at"),
        Index("idx_notif_type", "type"),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, receiver_id={self.receiver_id})>"


class PushToken(Base):
    """Push notification tokens (Expo)"""

    __tablename__ = "push_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Token
    token = Column(String(500), unique=True, nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # ios, android

    # Device info
    device_name = Column(String(255), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="push_tokens")

    __table_args__ = (
        Index("idx_push_token_user", "user_id"),
        Index("idx_push_token", "token"),
    )

    def __repr__(self):
        return f"<PushToken(id={self.id}, user_id={self.user_id}, platform={self.platform})>"
