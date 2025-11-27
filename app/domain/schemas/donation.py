"""Donation schemas"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class UpdateDonationRequest(BaseModel):
    """Request to update donation"""
    channel_id: str = Field(..., description="Channel ID code")
    amount: Decimal = Field(..., ge=0, description="Donation amount in EUR")
    hide_amount: bool = Field(default=False, description="Hide donation amount from public")


class UpdateDonationResponse(BaseModel):
    """Response for update donation"""
    success: bool


class UpdateDonationAmountRequest(BaseModel):
    """Request to update donation amount only"""
    channel_id: str = Field(..., description="Channel ID code")
    amount: Decimal = Field(..., ge=0, description="New donation amount in EUR")


class CreateDynamicSubscriptionRequest(BaseModel):
    """Request to create dynamic Stripe subscription"""
    product_name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0)
    currency: str = Field(default="EUR", max_length=3)
    user_id_code: str = Field(..., description="User ID code")
    description: Optional[str] = None
    success_url: str = Field(..., description="URL to redirect on success")
    cancel_url: str = Field(..., description="URL to redirect on cancel")


class CreateDynamicSubscriptionResponse(BaseModel):
    """Response for create dynamic subscription"""
    success: bool
    data: dict = Field(..., description="Contains checkout_url and session_id")


class CancelStripeSubscriptionRequest(BaseModel):
    """Request to cancel Stripe subscription"""
    channel_id: str = Field(..., description="Channel ID code")
    stripe_subscription_id: Optional[str] = None
    session_id: Optional[str] = None


class CancelStripeSubscriptionResponse(BaseModel):
    """Response for cancel subscription"""
    success: bool


class VerifyPaymentSessionResponse(BaseModel):
    """Response for verify payment session"""
    success: bool
    payment_status: str  # paid, unpaid, pending
    status: str  # complete, incomplete


class DonationCertificateResponse(BaseModel):
    """Response for donation certificate"""
    certificate_url: Optional[str] = None
    year: Optional[int] = None
    total_amount: Optional[Decimal] = None
    certificate_number: Optional[str] = None


class DebugDonationInfo(BaseModel):
    """Debug info for donations"""
    user_id: int
    channel_id: int
    channel_name: str
    amount: Decimal
    currency: str
    status: str
    stripe_subscription_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DebugDonationInfoResponse(BaseModel):
    """Response for debug donation info"""
    donations: list[DebugDonationInfo] = []
