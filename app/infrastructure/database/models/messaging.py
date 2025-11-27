from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Conversation(Base):
    """Conversations between users or in channels"""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Type
    type = Column(String(20), nullable=False)  # direct, channel

    # Relations
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True, index=True)

    # Info
    title = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    channel = relationship("Channel")
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_conversation_type", "type"),
        Index("idx_conversation_channel", "channel_id"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, type={self.type})>"


class ConversationParticipant(Base):
    """Participants in conversations"""

    __tablename__ = "conversation_participants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Read status
    last_read_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    unread_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User")

    __table_args__ = (
        Index("idx_participant_conv_user", "conversation_id", "user_id", unique=True),
    )

    def __repr__(self):
        return f"<ConversationParticipant(conversation_id={self.conversation_id}, user_id={self.user_id})>"


class Message(Base):
    """Messages in conversations"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Relations
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reply_to_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)

    # Content
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", nullable=False)  # text, image, video
    send_as_channel = Column(Boolean, default=False, nullable=False)

    # Status
    is_system_message = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    edited_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
    reply_to = relationship("Message", remote_side=[id], backref="replies")
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")
    reports = relationship("MessageReport", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_message_conv_created", "conversation_id", "created_at"),
        Index("idx_message_sender", "sender_id"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id})>"


class MessageReaction(Base):
    """Reactions to messages"""

    __tablename__ = "message_reactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Reaction
    emoji = Column(String(10), nullable=False)
    reaction_type = Column(String(50), default="like", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="reactions")
    user = relationship("User")

    __table_args__ = (
        Index("idx_reaction_msg_user", "message_id", "user_id"),
    )

    def __repr__(self):
        return f"<MessageReaction(message_id={self.message_id}, user_id={self.user_id}, emoji={self.emoji})>"


class MessageReport(Base):
    """Reports of inappropriate messages"""

    __tablename__ = "message_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Report
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, reviewed, resolved

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="reports")
    reporter = relationship("User")

    __table_args__ = (
        Index("idx_report_message", "message_id"),
        Index("idx_report_status", "status"),
    )

    def __repr__(self):
        return f"<MessageReport(id={self.id}, message_id={self.message_id}, status={self.status})>"
