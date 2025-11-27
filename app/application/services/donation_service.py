"""Donation service - Business logic"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import stripe

from app.application.repositories.donation_repository import DonationRepository
from app.infrastructure.stripe.stripe_service import StripeService
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
    DebugDonationInfo,
)


class DonationService:
    """Service for donation operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DonationRepository(session)
        self.stripe_service = StripeService()

    async def update_donation(
        self,
        request: UpdateDonationRequest,
        user_id: int
    ) -> UpdateDonationResponse:
        """Update or create donation to channel"""
        # Get channel
        channel = await self.repo.get_channel_by_id_code(request.channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        # Create or update donation
        await self.repo.create_or_update_donation(
            user_id=user_id,
            channel_id=channel.id,
            amount=request.amount,
            hide_amount=request.hide_amount
        )

        return UpdateDonationResponse(success=True)

    async def update_donation_amount(
        self,
        request: UpdateDonationAmountRequest,
        user_id: int
    ) -> UpdateDonationResponse:
        """Update donation amount only"""
        # Get channel
        channel = await self.repo.get_channel_by_id_code(request.channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        # Get existing donation
        existing = await self.repo.get_user_donation_to_channel(user_id, channel.id)
        if not existing:
            # Create new if doesn't exist
            await self.repo.create_or_update_donation(
                user_id=user_id,
                channel_id=channel.id,
                amount=request.amount
            )
        else:
            # Update amount
            await self.repo.create_or_update_donation(
                user_id=user_id,
                channel_id=channel.id,
                amount=request.amount,
                hide_amount=existing.hide_amount
            )

        return UpdateDonationResponse(success=True)

    async def create_dynamic_subscription(
        self,
        request: CreateDynamicSubscriptionRequest
    ) -> CreateDynamicSubscriptionResponse:
        """Create dynamic Stripe subscription checkout"""
        try:
            # Create Stripe product
            product = stripe.Product.create(
                name=request.product_name,
                description=request.description or ""
            )

            # Create price for the product
            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(request.price * 100),  # Convert to cents
                currency=request.currency.lower(),
                recurring={"interval": "month"}
            )

            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price": price.id,
                    "quantity": 1
                }],
                mode="subscription",
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                client_reference_id=request.user_id_code,
                metadata={
                    "user_id_code": request.user_id_code,
                    "product_name": request.product_name
                }
            )

            return CreateDynamicSubscriptionResponse(
                success=True,
                data={
                    "checkout_url": checkout_session.url,
                    "session_id": checkout_session.id
                }
            )

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    async def cancel_stripe_subscription(
        self,
        request: CancelStripeSubscriptionRequest,
        user_id: int
    ) -> CancelStripeSubscriptionResponse:
        """Cancel Stripe subscription"""
        # Get channel
        channel = await self.repo.get_channel_by_id_code(request.channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        # Get donation
        donation = await self.repo.get_user_donation_to_channel(user_id, channel.id)
        if not donation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active donation found"
            )

        # Cancel in Stripe
        subscription_id = request.stripe_subscription_id or donation.stripe_subscription_id
        if subscription_id:
            try:
                stripe.Subscription.delete(subscription_id)
            except stripe.error.StripeError as e:
                # Log but continue - still cancel in our database
                print(f"Stripe cancellation failed: {e}")

        # Cancel in database
        await self.repo.cancel_donation(user_id, channel.id)

        return CancelStripeSubscriptionResponse(success=True)

    async def verify_payment_session(
        self,
        session_id: str
    ) -> VerifyPaymentSessionResponse:
        """Verify Stripe payment session"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            payment_status = session.payment_status  # paid, unpaid, no_payment_required
            status_val = session.status  # complete, expired, open

            return VerifyPaymentSessionResponse(
                success=True,
                payment_status=payment_status,
                status=status_val
            )

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    async def get_donation_certificate(
        self,
        user_id: int,
        year: Optional[int] = None
    ) -> DonationCertificateResponse:
        """Get donation certificate for tax purposes"""
        if year is None:
            year = datetime.now().year

        # Check if certificate already exists
        existing = await self.repo.get_certificate(user_id, year)
        if existing:
            return DonationCertificateResponse(
                certificate_url=existing.certificate_url,
                year=existing.year,
                total_amount=existing.total_amount,
                certificate_number=existing.certificate_number
            )

        # Calculate total donations for the year
        total = await self.repo.get_total_donations_by_year(user_id, year)

        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No donations found for year {year}"
            )

        # Create certificate (URL would be generated by a PDF service)
        # For now, just save the record
        certificate = await self.repo.create_donation_certificate(
            user_id=user_id,
            year=year,
            total_amount=total,
            certificate_url=None  # Would generate PDF URL here
        )

        return DonationCertificateResponse(
            certificate_url=certificate.certificate_url,
            year=certificate.year,
            total_amount=certificate.total_amount,
            certificate_number=certificate.certificate_number
        )

    async def get_debug_donation_info(
        self,
        user_id: int
    ) -> DebugDonationInfoResponse:
        """Get all donation info for debugging"""
        donations = await self.repo.get_all_user_donations(user_id)

        donation_infos = []
        for donation in donations:
            # Get channel info
            result = await self.session.execute(
                f"SELECT name FROM channels WHERE id = {donation.channel_id}"
            )
            channel_name = result.scalar() or "Unknown"

            donation_infos.append(DebugDonationInfo(
                user_id=donation.user_id,
                channel_id=donation.channel_id,
                channel_name=channel_name,
                amount=donation.amount,
                currency=donation.currency,
                status=donation.status,
                stripe_subscription_id=donation.stripe_subscription_id,
                created_at=donation.created_at
            ))

        return DebugDonationInfoResponse(donations=donation_infos)
