"""OTP (One-Time Password) utilities"""
import random
import string
from datetime import datetime, timedelta

from app.infrastructure.config import settings


def generate_otp(length: int = 6) -> str:
    """
    Generate a random OTP code

    Args:
        length: Length of OTP code (default 6)

    Returns:
        str: OTP code (numeric)
    """
    return "".join(random.choices(string.digits, k=length))


def generate_registration_id() -> str:
    """
    Generate a unique registration session ID

    Returns:
        str: Registration ID
    """
    # Format: REG-{timestamp}-{random}
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"REG-{timestamp}-{random_part}"


def generate_session_id() -> str:
    """
    Generate a unique verification session ID

    Returns:
        str: Session ID
    """
    # Format: SES-{timestamp}-{random}
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"SES-{timestamp}-{random_part}"


def generate_ticket_code() -> str:
    """
    Generate a unique ticket code for events

    Returns:
        str: Ticket code
    """
    # Format: TKT-{timestamp}-{random}
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"TKT-{timestamp}-{random_part}"


def generate_id_code(prefix: str = "ID") -> str:
    """
    Generate a generic ID code

    Args:
        prefix: Prefix for the ID (e.g., "POST", "CMT", "CH")

    Returns:
        str: ID code
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{timestamp}-{random_part}"


def get_otp_expiry_time() -> datetime:
    """
    Get OTP expiration datetime

    Returns:
        datetime: Expiry time
    """
    return datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)


def get_registration_expiry_time() -> datetime:
    """
    Get registration session expiration datetime

    Returns:
        datetime: Expiry time
    """
    return datetime.utcnow() + timedelta(hours=settings.REGISTRATION_SESSION_EXPIRY_HOURS)


def is_expired(expiry_time: datetime) -> bool:
    """
    Check if a datetime has expired

    Args:
        expiry_time: Expiry datetime to check

    Returns:
        bool: True if expired
    """
    return datetime.utcnow() > expiry_time
