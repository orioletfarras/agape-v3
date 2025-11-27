from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Generic repository interface"""

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity"""
        pass

    @abstractmethod
    async def update(self, id: int, entity: T) -> Optional[T]:
        """Update existing entity"""
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Delete entity by ID"""
        pass
