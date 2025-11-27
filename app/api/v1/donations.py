"""Donations and Stripe endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.donation_service import DonationService
from app.domain.schemas.donation import (
    UpdateDonationRequest,
    UpdateDonationResponse,
    UpdateDonationAmountRequest,
    CreateDynamicSubscriptionRequest,
    CreateDynamicSubscriptionResponse,
    CancelStripeSubscriptionRequest,
    CancelStripeSubscriptionResponse,
    VerifyPaymentSessionResponse,
    DonationCertificateResponse,
    DebugDonationInfoResponse,
)

router = APIRouter(tags=["Donations"], prefix="")


# Dependency
async def get_donation_service(session: AsyncSession = Depends(get_db)) -> DonationService:
    return DonationService(session)


@router.post("/update-donation", response_model=UpdateDonationResponse, status_code=status.HTTP_200_OK)
async def update_donation(
    request: UpdateDonationRequest,
    current_user: User = Depends(get_current_user),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Update or create donation to a channel

    **Request:**
    ```json
    {
      "channel_id": "channel_abc123",
      "amount": 10.00,
      "hide_amount": false
    }
    ```

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await donation_service.update_donation(request, current_user.id)


@router.post("/update-donation-amount", response_model=UpdateDonationResponse, status_code=status.HTTP_200_OK)
async def update_donation_amount(
    request: UpdateDonationAmountRequest,
    current_user: User = Depends(get_current_user),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Update donation amount only

    **Request:**
    ```json
    {
      "channel_id": "channel_abc123",
      "amount": 15.00
    }
    ```

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await donation_service.update_donation_amount(request, current_user.id)


@router.post("/create-dynamic-subscription", response_model=CreateDynamicSubscriptionResponse, status_code=status.HTTP_200_OK)
async def create_dynamic_subscription(
    request: CreateDynamicSubscriptionRequest,
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Create dynamic Stripe subscription checkout session

    **Request:**
    ```json
    {
      "product_name": "Monthly Donation",
      "price": 10.00,
      "currency": "EUR",
      "user_id_code": "user_abc123",
      "description": "Monthly support",
      "success_url": "https://example.com/success",
      "cancel_url": "https://example.com/cancel"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "data": {
        "checkout_url": "https://checkout.stripe.com/...",
        "session_id": "cs_test_abc123"
      }
    }
    ```
    """
    return await donation_service.create_dynamic_subscription(request)


@router.post("/cancel-stripe-subscription", response_model=CancelStripeSubscriptionResponse, status_code=status.HTTP_200_OK)
async def cancel_stripe_subscription(
    request: CancelStripeSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Cancel Stripe subscription

    **Request:**
    ```json
    {
      "channel_id": "channel_abc123",
      "stripe_subscription_id": "sub_abc123",
      "session_id": "cs_test_abc123"
    }
    ```

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await donation_service.cancel_stripe_subscription(request, current_user.id)


@router.get("/verify-payment-session/{sessionId}", response_model=VerifyPaymentSessionResponse, status_code=status.HTTP_200_OK)
async def verify_payment_session(
    sessionId: str = Path(..., description="Stripe session ID"),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Verify Stripe payment session status

    **Response:**
    ```json
    {
      "success": true,
      "payment_status": "paid",
      "status": "complete"
    }
    ```
    """
    return await donation_service.verify_payment_session(sessionId)


@router.get("/donation-certificate", response_model=DonationCertificateResponse, status_code=status.HTTP_200_OK)
async def get_donation_certificate(
    year: Optional[int] = Query(None, description="Year for certificate (default: current year)"),
    current_user: User = Depends(get_current_user),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Get donation certificate for tax purposes

    **Query params:**
    - `year`: Year (optional, defaults to current year)

    **Response:**
    ```json
    {
      "certificate_url": "https://...",
      "year": 2025,
      "total_amount": 120.00,
      "certificate_number": "CERT-2025-ABC123"
    }
    ```
    """
    return await donation_service.get_donation_certificate(current_user.id, year)


@router.get("/debug-donation-info", response_model=DebugDonationInfoResponse, status_code=status.HTTP_200_OK)
async def get_debug_donation_info(
    current_user: User = Depends(get_current_user),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Get all donation info for debugging

    **Response:**
    ```json
    {
      "donations": [
        {
          "user_id": 1,
          "channel_id": 5,
          "channel_name": "Parish Channel",
          "amount": 10.00,
          "currency": "EUR",
          "status": "active",
          "stripe_subscription_id": "sub_abc123",
          "created_at": "2025-01-15T10:00:00"
        }
      ]
    }
    ```
    """
    return await donation_service.get_debug_donation_info(current_user.id)
