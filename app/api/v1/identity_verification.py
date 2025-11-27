"""Identity verification endpoints"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import secrets

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User, VerificationSession
from app.api.dependencies import get_current_user

router = APIRouter(tags=["Identity Verification"], prefix="")


@router.post("/create-verification-session", status_code=status.HTTP_200_OK)
async def create_verification_session(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Create identity verification session (e.g., Stripe Identity)

    **Response:**
    ```json
    {
      "success": true,
      "session_id": "vs_abc123xyz",
      "verification_url": "https://verify.stripe.com/..."
    }
    ```
    """
    # In a real implementation with Stripe Identity:
    # import stripe
    # verification_session = stripe.identity.VerificationSession.create(
    #     type='document',
    #     metadata={'user_id': str(current_user.id)},
    # )
    # session_id = verification_session.id
    # url = verification_session.url

    # For now, create a placeholder session
    session_id = f"vs_{secrets.token_urlsafe(16)}"
    verification_url = f"https://verify.stripe.com/start/{session_id}"

    # Save to database
    verification = VerificationSession(
        user_id=current_user.id,
        session_id=session_id,
        status="pending",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    session.add(verification)
    await session.commit()

    return {
        "success": True,
        "session_id": session_id,
        "verification_url": verification_url
    }


@router.get("/verify-identity-status/{sessionId}", status_code=status.HTTP_200_OK)
async def verify_identity_status(
    sessionId: str,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """
    Check identity verification status

    **Response:**
    ```json
    {
      "status": "verified",
      "message": "Identity verified successfully"
    }
    ```

    **Possible statuses:** pending, verified, failed
    """
    # In a real implementation:
    # import stripe
    # verification_session = stripe.identity.VerificationSession.retrieve(sessionId)
    # status = verification_session.status
    # last_error = verification_session.last_error

    # Get from database
    from sqlalchemy import select
    result = await db_session.execute(
        select(VerificationSession).where(
            VerificationSession.session_id == sessionId,
            VerificationSession.user_id == current_user.id
        )
    )
    verification = result.scalar_one_or_none()

    if not verification:
        return {
            "status": "pending",
            "message": "Verification session not found"
        }

    return {
        "status": verification.status,
        "message": f"Verification status: {verification.status}"
    }
