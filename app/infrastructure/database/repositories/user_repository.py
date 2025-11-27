from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import UserEntity
from app.domain.interfaces import IUserRepository
from app.infrastructure.database.models import UserModel


class UserRepository(IUserRepository):
    """SQLAlchemy implementation of User Repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: UserModel) -> UserEntity:
        """Convert database model to domain entity"""
        return UserEntity(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: UserEntity) -> UserModel:
        """Convert domain entity to database model"""
        return UserModel(
            id=entity.id,
            email=entity.email,
            full_name=entity.full_name,
            is_active=entity.is_active,
        )

    async def get_by_id(self, id: int) -> Optional[UserEntity]:
        """Get user by ID"""
        result = await self.session.execute(select(UserModel).where(UserModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        """Get all users with pagination"""
        result = await self.session.execute(select(UserModel).offset(skip).limit(limit))
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def create(self, entity: UserEntity) -> UserEntity:
        """Create new user"""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def update(self, id: int, entity: UserEntity) -> Optional[UserEntity]:
        """Update existing user"""
        result = await self.session.execute(select(UserModel).where(UserModel.id == id))
        model = result.scalar_one_or_none()

        if not model:
            return None

        model.email = entity.email
        model.full_name = entity.full_name
        model.is_active = entity.is_active

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: int) -> bool:
        """Delete user by ID"""
        result = await self.session.execute(select(UserModel).where(UserModel.id == id))
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.commit()
        return True

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email"""
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        return result.scalar_one_or_none() is not None
