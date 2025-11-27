from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class UserSetting(Base):
    """User settings key-value store"""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Setting
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="settings")

    __table_args__ = (
        Index("idx_user_setting", "user_id", "key", unique=True),
    )

    def __repr__(self):
        return f"<UserSetting(user_id={self.user_id}, key={self.key})>"
