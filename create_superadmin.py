"""
Script to create superadmin user
"""
import asyncio
from sqlalchemy import select
from app.infrastructure.database import db
from app.infrastructure.database.models import User
from app.infrastructure.security import hash_password
from datetime import datetime

async def create_superadmin():
    # Initialize database
    db.initialize()

    async for session in db.get_session():
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == "oriol@penwin.org")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Usuario ya existe con ID: {existing_user.id}")
            print(f"Email: {existing_user.email}")
            print(f"Username: {existing_user.username}")
            return existing_user.id

        # Create new superadmin user
        user = User(
            email="oriol@penwin.org",
            username="oriol",
            password_hash=hash_password("20141130"),
            nombre="Oriol",
            apellidos="Farras",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        print(f"✓ Usuario superadmin creado exitosamente!")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")

        return user.id

    await db.close()

if __name__ == "__main__":
    asyncio.run(create_superadmin())
