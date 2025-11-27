"""Prayer Life and Automatic Channels models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class AutomaticChannelContent(Base):
    """Content for automatic prayer channels (daily readings, saints, prayers)"""
    __tablename__ = "automatic_channel_content"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=True, index=True)  # For daily content

    # Content fields (flexible for different types)
    title = Column(String(500), nullable=True)
    text = Column(Text, nullable=True)
    audio_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)

    # For saints
    name = Column(String(255), nullable=True)
    biography = Column(Text, nullable=True)

    # Metadata
    content_type = Column(String(50), nullable=False, index=True)  # reading, saint, prayer, rosary
    language = Column(String(10), default="es", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    channel = relationship("Channel", backref="automatic_content")

    __table_args__ = (
        Index("idx_channel_date", "channel_id", "date"),
        Index("idx_content_type", "content_type"),
    )


class UserChannelOrder(Base):
    """User's custom ordering of automatic channels"""
    __tablename__ = "user_channel_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id_code = Column(String(50), nullable=False)
    order_position = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="channel_orders")

    __table_args__ = (
        Index("idx_user_channel_order", "user_id", "channel_id_code", unique=True),
    )


class PrayerLifeWebAccess(Base):
    """Temporary web access tokens for prayer life"""
    __tablename__ = "prayer_life_web_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    web_url = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="prayer_web_tokens")

    __table_args__ = (
        Index("idx_token_expires", "token", "expires_at"),
    )
