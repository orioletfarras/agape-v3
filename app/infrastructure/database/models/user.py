from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class User(Base):
    """User model - Tabla completa de usuarios"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile fields
    nombre = Column(String(100), nullable=True)
    apellidos = Column(String(100), nullable=True)
    fecha_nacimiento = Column(DateTime, nullable=True)
    genero = Column(String(20), nullable=True)
    telefono = Column(String(50), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)

    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)

    # Organization & Parish
    primary_organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    parish_id = Column(Integer, ForeignKey("parishes.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    primary_organization = relationship("Organization", back_populates="members", foreign_keys=[primary_organization_id])
    parish = relationship("Parish", back_populates="members")
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    notifications_sent = relationship("Notification", back_populates="sender", foreign_keys="Notification.sender_id")
    notifications_received = relationship("Notification", back_populates="receiver", foreign_keys="Notification.receiver_id")
    channels_created = relationship("Channel", back_populates="creator")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
    push_tokens = relationship("PushToken", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # Many-to-Many relationships
    channel_subscriptions = relationship("ChannelSubscription", back_populates="user", cascade="all, delete-orphan")
    channel_admins = relationship("ChannelAdmin", back_populates="user", cascade="all, delete-orphan")
    organization_memberships = relationship("UserOrganization", back_populates="user", cascade="all, delete-orphan")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")
    followers = relationship("Follow", foreign_keys="Follow.followed_id", back_populates="followed", cascade="all, delete-orphan")
    event_registrations = relationship("EventRegistration", back_populates="user", cascade="all, delete-orphan")
    post_likes = relationship("PostLike", back_populates="user", cascade="all, delete-orphan")
    post_prays = relationship("PostPray", back_populates="user", cascade="all, delete-orphan")
    post_favorites = relationship("PostFavorite", back_populates="user", cascade="all, delete-orphan")
    hidden_posts = relationship("HiddenPost", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_username", "username"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
