from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Channel(Base):
    """Channel model - Canales de contenido"""

    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)

    # Settings
    is_automatic = Column(Boolean, default=False, nullable=False)
    category = Column(String(100), nullable=True)
    language = Column(String(10), default="es", nullable=False)

    # Organization
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Donation settings
    donation_amount = Column(Numeric(10, 2), default=0, nullable=False)
    hide_amount = Column(Boolean, default=False, nullable=False)

    # Stripe
    stripe_subscription_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="channels")
    creator = relationship("User", back_populates="channels_created")
    posts = relationship("Post", back_populates="channel", cascade="all, delete-orphan")
    subscriptions = relationship("ChannelSubscription", back_populates="channel", cascade="all, delete-orphan")
    admins = relationship("ChannelAdmin", back_populates="channel", cascade="all, delete-orphan")
    settings = relationship("ChannelSetting", back_populates="channel", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="channel", cascade="all, delete-orphan")
    alerts = relationship("ChannelAlert", back_populates="channel", cascade="all, delete-orphan")
    polls = relationship("Poll", back_populates="channel", cascade="all, delete-orphan")
    hidden_by_users = relationship("HiddenChannel", back_populates="channel", cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="channel", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_channel_id_code", "id_code"),
        Index("idx_channel_name", "name"),
        Index("idx_channel_category", "category"),
    )

    def __repr__(self):
        return f"<Channel(id={self.id}, id_code={self.id_code}, name={self.name})>"


class ChannelSubscription(Base):
    """Many-to-Many: Users subscribed to Channels"""

    __tablename__ = "channel_subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="channel_subscriptions")
    channel = relationship("Channel", back_populates="subscriptions")

    __table_args__ = (
        Index("idx_user_channel_sub", "user_id", "channel_id", unique=True),
    )

    def __repr__(self):
        return f"<ChannelSubscription(user_id={self.user_id}, channel_id={self.channel_id})>"


class ChannelAdmin(Base):
    """Many-to-Many: Channel administrators"""

    __tablename__ = "channel_admins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="channel_admins")
    channel = relationship("Channel", back_populates="admins")

    __table_args__ = (
        Index("idx_user_channel_admin", "user_id", "channel_id", unique=True),
    )

    def __repr__(self):
        return f"<ChannelAdmin(user_id={self.user_id}, channel_id={self.channel_id})>"


class ChannelSetting(Base):
    """Channel settings key-value store"""

    __tablename__ = "channel_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    channel = relationship("Channel", back_populates="settings")

    __table_args__ = (
        Index("idx_channel_setting", "channel_id", "key", unique=True),
    )

    def __repr__(self):
        return f"<ChannelSetting(channel_id={self.channel_id}, key={self.key})>"


class HiddenChannel(Base):
    """Channels hidden by users"""

    __tablename__ = "hidden_channels"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
    channel = relationship("Channel", back_populates="hidden_by_users")

    __table_args__ = (
        Index("idx_user_hidden_channel", "user_id", "channel_id", unique=True),
    )

    def __repr__(self):
        return f"<HiddenChannel(user_id={self.user_id}, channel_id={self.channel_id})>"


class ChannelAlert(Base):
    """Alerts sent by channels to subscribers"""

    __tablename__ = "channel_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    channel = relationship("Channel", back_populates="alerts")

    __table_args__ = (
        Index("idx_channel_alert_created", "channel_id", "created_at"),
    )

    def __repr__(self):
        return f"<ChannelAlert(id={self.id}, channel_id={self.channel_id})>"
