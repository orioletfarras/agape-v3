"""Debug and logging models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.database.base import Base


class DebugLog(Base):
    """Client debug logs"""
    __tablename__ = "debug_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    log_level = Column(String(20), default="info")  # info, warning, error, debug
    message = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # JSON string with additional context
    source = Column(String(100), nullable=True)  # mobile, web, etc.
    device_info = Column(Text, nullable=True)  # JSON string with device info
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", backref="debug_logs")
