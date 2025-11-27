from abc import abstractmethod
from typing import Optional
from app.domain.interfaces.repository import IRepository
from app.domain.entities import UserEntity


class IUserRepository(IRepository[UserEntity]):
    """User repository interface"""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email"""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        pass
