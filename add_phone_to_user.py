"""
Script to add phone number to user oriol@penwin.org
"""
import asyncio
from sqlalchemy import select
from app.infrastructure.database import db
from app.infrastructure.database.models import User

async def add_phone():
    # Initialize database
    db.initialize()

    async for session in db.get_session():
        # Get user
        result = await session.execute(
            select(User).where(User.email == "oriol@penwin.org")
        )
        user = result.scalar_one_or_none()

        if not user:
            print("❌ Usuario no encontrado")
            return

        print(f"✓ Usuario encontrado: {user.email} (ID: {user.id})")
        print(f"  Teléfono actual: {user.telefono}")

        # Update phone
        user.telefono = "+34625634948"
        await session.commit()

        print(f"✅ Teléfono actualizado: {user.telefono}")

    await db.close()

if __name__ == "__main__":
    asyncio.run(add_phone())
