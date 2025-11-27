"""Event domain schemas"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreateEventRequest(BaseModel):
    """Request to create a new event"""
    channel_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    event_date: datetime
    end_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    max_attendees: Optional[int] = Field(None, ge=1)
    registration_deadline: Optional[datetime] = None
    requires_payment: bool = False
    price: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field("EUR", max_length=3)


class UpdateEventRequest(BaseModel):
    """Request to update an event"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    event_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    max_attendees: Optional[int] = Field(None, ge=1)
    registration_deadline: Optional[datetime] = None
    requires_payment: Optional[bool] = None
    price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)


class RegisterEventRequest(BaseModel):
    """Request to register for an event"""
    event_id: int


class ApplyDiscountRequest(BaseModel):
    """Request to apply discount code"""
    code: str = Field(..., min_length=1, max_length=50)


class CreateDiscountCodeRequest(BaseModel):
    """Request to create discount code"""
    event_id: int
    code: str = Field(..., min_length=1, max_length=50)
    discount_type: str = Field(..., pattern="^(percentage|fixed)$")
    discount_value: Decimal = Field(..., ge=0)
    max_uses: Optional[int] = Field(None, ge=1)
    valid_until: Optional[datetime] = None


class CreateEventAlertRequest(BaseModel):
    """Request to create event alert"""
    event_id: int
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class EventResponse(BaseModel):
    """Basic event response"""
    id: int
    channel_id: int
    name: str
    description: Optional[str] = None
    event_date: datetime
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    max_attendees: Optional[int] = None
    registration_deadline: Optional[datetime] = None
    requires_payment: bool
    price: Optional[Decimal] = None
    currency: str
    created_at: datetime
    updated_at: datetime

    # Counts
    registered_count: int = 0

    # Current user status
    is_registered: bool = False
    has_paid: bool = False

    # Related data
    channel: Optional["ChannelBasicResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class ChannelBasicResponse(BaseModel):
    """Basic channel info for event"""
    id: int
    name: str
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserBasicResponse(BaseModel):
    """Basic user info"""
    id: int
    username: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    profile_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    """Paginated list of events"""
    events: List[EventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class EventRegistrationResponse(BaseModel):
    """Event registration response"""
    id: int
    event_id: int
    user_id: int
    registered_at: datetime
    payment_status: str
    payment_amount: Optional[Decimal] = None
    user: Optional[UserBasicResponse] = None

    model_config = ConfigDict(from_attributes=True)


class EventRegistrationActionResponse(BaseModel):
    """Response after registration action"""
    success: bool
    message: str
    registration: Optional[EventRegistrationResponse] = None


class EventTransactionResponse(BaseModel):
    """Event transaction response"""
    id: int
    event_id: int
    user_id: int
    registration_id: int
    amount: Decimal
    currency: str
    payment_method: str
    stripe_payment_intent_id: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscountCodeResponse(BaseModel):
    """Discount code response"""
    id: int
    event_id: int
    code: str
    discount_type: str
    discount_value: Decimal
    max_uses: Optional[int] = None
    times_used: int
    valid_until: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplyDiscountResponse(BaseModel):
    """Response after applying discount"""
    success: bool
    message: str
    original_price: Decimal
    discount_amount: Decimal
    final_price: Decimal


class EventAlertResponse(BaseModel):
    """Event alert response"""
    id: int
    event_id: int
    title: str
    message: str
    created_by: int
    created_at: datetime
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EventStatsResponse(BaseModel):
    """Event statistics"""
    registered_count: int
    paid_count: int
    pending_payment_count: int
    total_revenue: Decimal
    available_spots: Optional[int] = None


class EventDeleteResponse(BaseModel):
    """Response after deleting event"""
    success: bool
    message: str


class PaymentIntentResponse(BaseModel):
    """Stripe payment intent response"""
    client_secret: str
    amount: Decimal
    currency: str


# ============================================================
# FILTER/QUERY SCHEMAS
# ============================================================

class EventFilters(BaseModel):
    """Filters for listing events"""
    channel_id: Optional[int] = None
    upcoming_only: bool = True
    registered_only: bool = False
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
