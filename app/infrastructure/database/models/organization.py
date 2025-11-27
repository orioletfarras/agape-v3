from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Organization(Base):
    """Organization model - Organizaciones (parroquias, diocesis, etc)"""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    image_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("User", back_populates="primary_organization", foreign_keys="User.primary_organization_id")
    user_organizations = relationship("UserOrganization", back_populates="organization", cascade="all, delete-orphan")
    channels = relationship("Channel", back_populates="organization")

    __table_args__ = (
        Index("idx_organization_name", "name"),
    )

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"


class Parish(Base):
    """Parish model - Parroquias"""

    __tablename__ = "parishes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=True)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("User", back_populates="parish")

    __table_args__ = (
        Index("idx_parish_name", "name"),
    )

    def __repr__(self):
        return f"<Parish(id={self.id}, name={self.name})>"


class UserOrganization(Base):
    """Many-to-Many relationship between Users and Organizations"""

    __tablename__ = "user_organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="organization_memberships")
    organization = relationship("Organization", back_populates="user_organizations")

    __table_args__ = (
        Index("idx_user_org", "user_id", "organization_id", unique=True),
    )

    def __repr__(self):
        return f"<UserOrganization(user_id={self.user_id}, org_id={self.organization_id})>"
