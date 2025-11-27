from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Comment(Base):
    """Comment model - Comentarios en posts"""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_code = Column(String(50), unique=True, nullable=False, index=True)

    # Content
    text_comment = Column(Text, nullable=False)

    # Relations
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True, index=True)  # For replies

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id], backref="replies")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_comment_post_created", "post_id", "created_at"),
        Index("idx_comment_author", "author_id"),
        Index("idx_comment_parent", "parent_comment_id"),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id})>"


class CommentLike(Base):
    """Comment likes"""

    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
    comment = relationship("Comment", back_populates="likes")

    __table_args__ = (
        Index("idx_user_comment_like", "user_id", "comment_id", unique=True),
    )

    def __repr__(self):
        return f"<CommentLike(user_id={self.user_id}, comment_id={self.comment_id})>"
