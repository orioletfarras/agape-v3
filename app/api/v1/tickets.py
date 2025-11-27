"""Tickets and Apple Wallet passes endpoints"""
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User, EventRegistration
from app.api.dependencies import get_current_user

router = APIRouter(tags=["Tickets"], prefix="")


@router.get("/tickets", status_code=status.HTTP_200_OK)
async def get_user_tickets(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get all tickets for current user

    **Response:**
    ```json
    {
      "tickets": [
        {
          "id": 1,
          "event_id": 5,
          "event_title": "Youth Conference 2025",
          "ticket_code": "ABC123XYZ",
          "status": "active"
        }
      ]
    }
    ```
    """
    result = await session.execute(
        select(EventRegistration)
        .where(EventRegistration.user_id == current_user.id)
        .order_by(EventRegistration.created_at.desc())
    )
    registrations = result.scalars().all()

    tickets = []
    for reg in registrations:
        # Get event details
        from app.infrastructure.database.models import Event
        event_result = await session.execute(
            select(Event).where(Event.id == reg.event_id)
        )
        event = event_result.scalar_one_or_none()

        if event:
            tickets.append({
                "id": reg.id,
                "event_id": event.id,
                "event_title": event.title,
                "ticket_code": reg.ticket_code,
                "status": reg.payment_status
            })

    return {"tickets": tickets}


@router.get("/passes/{ticketId}.pkpass", status_code=status.HTTP_200_OK)
async def get_apple_wallet_pass(
    ticketId: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Generate and return Apple Wallet pass file (.pkpass)

    **Returns:** Apple Wallet pass file (application/vnd.apple.pkpass)
    """
    # Get ticket/registration
    result = await session.execute(
        select(EventRegistration).where(
            EventRegistration.id == ticketId,
            EventRegistration.user_id == current_user.id
        )
    )
    registration = result.scalar_one_or_none()

    if not registration:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Get event details
    from app.infrastructure.database.models import Event
    event_result = await session.execute(
        select(Event).where(Event.id == registration.event_id)
    )
    event = event_result.scalar_one_or_none()

    # In a real implementation, you would:
    # 1. Generate a proper .pkpass file using Apple Wallet format
    # 2. Sign it with your Apple Developer certificate
    # 3. Return the binary data

    # For now, return a placeholder response
    # You would use a library like 'wallet' or 'passbook' for Python
    pass_data = b"PLACEHOLDER_PKPASS_DATA"  # Would be actual .pkpass file

    return Response(
        content=pass_data,
        media_type="application/vnd.apple.pkpass",
        headers={
            "Content-Disposition": f"attachment; filename=ticket_{ticketId}.pkpass"
        }
    )
