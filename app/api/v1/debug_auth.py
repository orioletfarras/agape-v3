"""Debug authentication endpoints - ONLY FOR DEVELOPMENT"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database import get_db
from app.infrastructure.database.models import OTPCode

router = APIRouter(tags=["Debug"], prefix="/debug")


@router.get("/latest-otp/{email}")
async def get_latest_otp(
    email: str,
    session: AsyncSession = Depends(get_db)
):
    """Get latest OTP code for an email (DEBUG ONLY)"""
    result = await session.execute(
        select(OTPCode)
        .where(OTPCode.email == email, OTPCode.is_used == False)
        .order_by(OTPCode.created_at.desc())
        .limit(1)
    )
    otp = result.scalar_one_or_none()
    
    if otp:
        return {
            "email": otp.email,
            "code": otp.code,
            "method": otp.method,
            "purpose": otp.purpose,
            "expires_at": otp.expires_at,
            "created_at": otp.created_at
        }
    
    return {"error": "No OTP found for this email"}
