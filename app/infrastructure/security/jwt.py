"""JWT token utilities"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (optional)

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (optional)

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        dict: Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload

    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and check its type

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        dict: Token payload if valid, None otherwise
    """
    payload = decode_token(token)

    if not payload:
        return None

    # Verify token type
    if payload.get("type") != token_type:
        logger.warning(f"Invalid token type. Expected {token_type}, got {payload.get('type')}")
        return None

    # Check expiration
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
        logger.warning("Token has expired")
        return None

    return payload


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from a JWT token

    Args:
        token: JWT token string

    Returns:
        int: User ID or None if invalid
    """
    payload = verify_token(token, token_type="access")

    if not payload:
        return None

    return payload.get("sub")


def create_token_pair(user_id: int, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user

    Args:
        user_id: User ID
        additional_data: Additional data to include in tokens

    Returns:
        dict: Dictionary with access_token and refresh_token
    """
    token_data = {"sub": user_id}

    if additional_data:
        token_data.update(additional_data)

    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
