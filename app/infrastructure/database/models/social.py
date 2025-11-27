from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Follow(Base):
    """Follow relationships between users"""

    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Status
    status = Column(String(50), default="accepted", nullable=False)  # pending, accepted, rejected

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)

    # Relationships
    follower = relationship("User", back_populates="following", foreign_keys=[follower_id])
    followed = relationship("User", back_populates="followers", foreign_keys=[followed_id])

    __table_args__ = (
        Index("idx_follow_follower_followed", "follower_id", "followed_id", unique=True),
        Index("idx_follow_status", "status"),
    )

    def __repr__(self):
        return f"<Follow(follower_id={self.follower_id}, followed_id={self.followed_id}, status={self.status})>"


class Story(Base):
    """User stories (temporary content)"""

    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Content
    media_url = Column(String(500), nullable=False)
    media_type = Column(String(20), default="image", nullable=False)  # image, video

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("idx_story_user_created", "user_id", "created_at"),
        Index("idx_story_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<Story(id={self.id}, user_id={self.user_id})>"


class Poll(Base):
    """Polls in channels"""

    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Content
    question = Column(String(500), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    channel = relationship("Channel", back_populates="polls")
    creator = relationship("User")
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    votes = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_poll_channel_created", "channel_id", "created_at"),
    )

    def __repr__(self):
        return f"<Poll(id={self.id}, channel_id={self.channel_id})>"


class PollOption(Base):
    """Options in polls"""

    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False, index=True)

    # Content
    text = Column(String(255), nullable=False)
    order = Column(Integer, default=0, nullable=False)

    # Relationships
    poll = relationship("Poll", back_populates="options")
    votes = relationship("PollVote", back_populates="option", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_poll_option_poll", "poll_id", "order"),
    )

    def __repr__(self):
        return f"<PollOption(id={self.id}, poll_id={self.poll_id}, text={self.text})>"


class PollVote(Base):
    """Votes on poll options"""

    __tablename__ = "poll_votes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False, index=True)
    option_id = Column(Integer, ForeignKey("poll_options.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    poll = relationship("Poll", back_populates="votes")
    option = relationship("PollOption", back_populates="votes")
    user = relationship("User")

    __table_args__ = (
        Index("idx_poll_vote_user_poll", "user_id", "poll_id", unique=True),
    )

    def __repr__(self):
        return f"<PollVote(poll_id={self.poll_id}, option_id={self.option_id}, user_id={self.user_id})>"
