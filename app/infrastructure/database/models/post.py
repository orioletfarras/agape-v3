from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base
from app.infrastructure.security import generate_id_code


class Post(Base):
    """Post model - Posts/publicaciones"""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_code = Column(String(50), unique=True, nullable=False, index=True, default=lambda: generate_id_code("POST"))

    # Content
    text = Column(Text, nullable=False)
    images = Column(JSON, nullable=True)  # Array de URLs
    video_url = Column(String(500), nullable=True)
    posttag = Column(String(100), nullable=True, index=True)

    # Relations
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)

    # Status
    is_published = Column(Boolean, default=True, nullable=False)
    is_reviewed = Column(Boolean, default=False, nullable=False)
    is_suspected = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    author = relationship("User", back_populates="posts")
    channel = relationship("Channel", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    prays = relationship("PostPray", back_populates="post", cascade="all, delete-orphan")
    favorites = relationship("PostFavorite", back_populates="post", cascade="all, delete-orphan")
    hidden_by_users = relationship("HiddenPost", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_post_channel_created", "channel_id", "created_at"),
        Index("idx_post_author", "author_id"),
        Index("idx_post_id_code", "id_code"),
    )

    def __repr__(self):
        return f"<Post(id={self.id}, id_code={self.id_code})>"


class PostLike(Base):
    """Post likes"""

    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="post_likes")
    post = relationship("Post", back_populates="likes")

    __table_args__ = (
        Index("idx_user_post_like", "user_id", "post_id", unique=True),
    )

    def __repr__(self):
        return f"<PostLike(user_id={self.user_id}, post_id={self.post_id})>"


class PostPray(Base):
    """Post prayers"""

    __tablename__ = "post_prays"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="post_prays")
    post = relationship("Post", back_populates="prays")

    __table_args__ = (
        Index("idx_user_post_pray", "user_id", "post_id", unique=True),
    )

    def __repr__(self):
        return f"<PostPray(user_id={self.user_id}, post_id={self.post_id})>"


class PostFavorite(Base):
    """Post favorites"""

    __tablename__ = "post_favorites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="post_favorites")
    post = relationship("Post", back_populates="favorites")

    __table_args__ = (
        Index("idx_user_post_fav", "user_id", "post_id", unique=True),
    )

    def __repr__(self):
        return f"<PostFavorite(user_id={self.user_id}, post_id={self.post_id})>"


class HiddenPost(Base):
    """Posts hidden by users"""

    __tablename__ = "hidden_posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="hidden_posts")
    post = relationship("Post", back_populates="hidden_by_users")

    __table_args__ = (
        Index("idx_user_hidden_post", "user_id", "post_id", unique=True),
    )

    def __repr__(self):
        return f"<HiddenPost(user_id={self.user_id}, post_id={self.post_id})>"
