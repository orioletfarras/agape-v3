"""Donation repository - Database operations"""
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import select, and_, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    Donation,
    DonationCertificate,
    Channel,
    User
)


class DonationRepository:
    """Repository for donation operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_channel_by_id_code(self, id_code: str) -> Optional[Channel]:
        """Get channel by id_code"""
        result = await self.session.execute(
            select(Channel).where(Channel.id_code == id_code)
        )
        return result.scalar_one_or_none()

    async def get_user_donation_to_channel(
        self,
        user_id: int,
        channel_id: int
    ) -> Optional[Donation]:
        """Get user's donation to specific channel"""
        result = await self.session.execute(
            select(Donation).where(
                and_(
                    Donation.user_id == user_id,
                    Donation.channel_id == channel_id,
                    Donation.status == "active"
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update_donation(
        self,
        user_id: int,
        channel_id: int,
        amount: Decimal,
        hide_amount: bool = False,
        stripe_subscription_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Donation:
        """Create or update donation"""
        existing = await self.get_user_donation_to_channel(user_id, channel_id)

        if existing:
            # Update existing
            existing.amount = amount
            existing.hide_amount = hide_amount
            if stripe_subscription_id:
                existing.stripe_subscription_id = stripe_subscription_id
            if stripe_customer_id:
                existing.stripe_customer_id = stripe_customer_id
            if session_id:
                existing.session_id = session_id
            existing.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new
            donation = Donation(
                user_id=user_id,
                channel_id=channel_id,
                amount=amount,
                hide_amount=hide_amount,
                stripe_subscription_id=stripe_subscription_id,
                stripe_customer_id=stripe_customer_id,
                session_id=session_id,
                status="active",
                payment_status="pending",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(donation)
            await self.session.commit()
            await self.session.refresh(donation)
            return donation

    async def cancel_donation(
        self,
        user_id: int,
        channel_id: int
    ) -> bool:
        """Cancel user's donation to channel"""
        donation = await self.get_user_donation_to_channel(user_id, channel_id)
        if not donation:
            return False

        donation.status = "cancelled"
        donation.cancelled_at = datetime.utcnow()
        donation.updated_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def get_donation_by_subscription_id(
        self,
        subscription_id: str
    ) -> Optional[Donation]:
        """Get donation by Stripe subscription ID"""
        result = await self.session.execute(
            select(Donation).where(
                Donation.stripe_subscription_id == subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def get_donation_by_session_id(
        self,
        session_id: str
    ) -> Optional[Donation]:
        """Get donation by session ID"""
        result = await self.session.execute(
            select(Donation).where(Donation.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_user_donations_by_year(
        self,
        user_id: int,
        year: int
    ) -> List[Donation]:
        """Get all donations by user for a specific year"""
        result = await self.session.execute(
            select(Donation).where(
                and_(
                    Donation.user_id == user_id,
                    extract('year', Donation.created_at) == year,
                    Donation.payment_status == "paid"
                )
            )
        )
        return list(result.scalars().all())

    async def get_total_donations_by_year(
        self,
        user_id: int,
        year: int
    ) -> Decimal:
        """Calculate total donations by user for a year"""
        result = await self.session.execute(
            select(func.sum(Donation.amount)).where(
                and_(
                    Donation.user_id == user_id,
                    extract('year', Donation.created_at) == year,
                    Donation.payment_status == "paid"
                )
            )
        )
        total = result.scalar()
        return Decimal(total) if total else Decimal("0.00")

    async def create_donation_certificate(
        self,
        user_id: int,
        year: int,
        total_amount: Decimal,
        certificate_url: Optional[str] = None
    ) -> DonationCertificate:
        """Create donation certificate"""
        # Generate certificate number
        import secrets
        certificate_number = f"CERT-{year}-{secrets.token_hex(8).upper()}"

        certificate = DonationCertificate(
            user_id=user_id,
            year=year,
            total_amount=total_amount,
            certificate_url=certificate_url,
            certificate_number=certificate_number,
            generated_at=datetime.utcnow()
        )
        self.session.add(certificate)
        await self.session.commit()
        await self.session.refresh(certificate)
        return certificate

    async def get_certificate(
        self,
        user_id: int,
        year: int
    ) -> Optional[DonationCertificate]:
        """Get certificate for user and year"""
        result = await self.session.execute(
            select(DonationCertificate).where(
                and_(
                    DonationCertificate.user_id == user_id,
                    DonationCertificate.year == year
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_all_user_donations(self, user_id: int) -> List[Donation]:
        """Get all donations for a user (for debugging)"""
        result = await self.session.execute(
            select(Donation)
            .where(Donation.user_id == user_id)
            .order_by(Donation.created_at.desc())
        )
        return list(result.scalars().all())
