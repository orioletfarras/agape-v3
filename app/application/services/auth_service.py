"""Authentication service with business logic"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.infrastructure.database.models import (
    User,
    OTPCode,
    RegistrationSession,
    RefreshToken,
    UserOrganization,
)
from app.infrastructure.security import (
    hash_password,
    verify_password,
    create_token_pair,
    verify_token,
    generate_otp,
    generate_registration_id,
    get_otp_expiry_time,
    get_registration_expiry_time,
    is_expired,
)
from app.infrastructure.aws import ses_service, sns_service

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user with email and password

        Args:
            email: User email
            password: User password

        Returns:
            dict: Token pair and user info

        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        # Update last login
        user.last_login = datetime.utcnow()
        await self.session.commit()

        # Generate tokens
        tokens = create_token_pair(user.id)

        # Store refresh token in database
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token=tokens["refresh_token"],
            expires_at=datetime.utcnow() + get_registration_expiry_time(),
        )
        self.session.add(refresh_token_record)
        await self.session.commit()

        return {
            "success": True,
            "token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            },
        }

    async def register_start(self, email: str, password: str) -> Dict[str, Any]:
        """
        Start registration process

        Args:
            email: User email
            password: User password

        Returns:
            dict: Registration ID

        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        result = await self.session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Generate registration ID
        registration_id = generate_registration_id()

        # Hash password
        password_hash = hash_password(password)

        # Create registration session
        reg_session = RegistrationSession(
            registration_id=registration_id,
            email=email,
            password_hash=password_hash,
            expires_at=get_registration_expiry_time(),
        )
        self.session.add(reg_session)
        await self.session.commit()

        # Generate and send OTP
        otp_code = generate_otp()
        otp = OTPCode(
            email=email,
            code=otp_code,
            method="email",
            purpose="register",
            expires_at=get_otp_expiry_time(),
        )
        self.session.add(otp)
        await self.session.commit()

        # Send OTP email
        await ses_service.send_otp_email(email, otp_code, "registro")

        return {
            "success": True,
            "message": "Verification code sent to your email",
            "registration_id": registration_id,
        }

    async def register_verify_email(self, registration_id: str, code: str) -> Dict[str, Any]:
        """Verify email with OTP code"""
        # Get registration session
        result = await self.session.execute(
            select(RegistrationSession).where(
                RegistrationSession.registration_id == registration_id,
                RegistrationSession.is_completed == False,
            )
        )
        reg_session = result.scalar_one_or_none()

        if not reg_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration session not found or already completed",
            )

        # Check if expired
        if is_expired(reg_session.expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration session expired",
            )

        # Get OTP
        result = await self.session.execute(
            select(OTPCode).where(
                OTPCode.email == reg_session.email,
                OTPCode.code == code,
                OTPCode.purpose == "register",
                OTPCode.is_used == False,
            )
        )
        otp = result.scalar_one_or_none()

        if not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        # Check if OTP expired
        if is_expired(otp.expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code expired",
            )

        # Mark OTP as used
        otp.is_used = True
        otp.used_at = datetime.utcnow()

        # Mark email as verified
        reg_session.email_verified = True
        await self.session.commit()

        return {
            "success": True,
            "message": "Email verified successfully",
        }

    async def register_complete(
        self, registration_id: str, username: str, name: str
    ) -> Dict[str, Any]:
        """Complete registration"""
        # Get registration session
        result = await self.session.execute(
            select(RegistrationSession).where(
                RegistrationSession.registration_id == registration_id,
                RegistrationSession.is_completed == False,
                RegistrationSession.email_verified == True,
            )
        )
        reg_session = result.scalar_one_or_none()

        if not reg_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration session not found or email not verified",
            )

        # Check if username already exists
        result = await self.session.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

        # Create user
        user = User(
            email=reg_session.email,
            username=username,
            password_hash=reg_session.password_hash,
            nombre=name,
            is_verified=True,
        )
        self.session.add(user)

        # Mark registration as completed
        reg_session.is_completed = True
        reg_session.completed_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(user)

        # Generate tokens
        tokens = create_token_pair(user.id)

        # Send welcome email
        await ses_service.send_welcome_email(user.email, user.username)

        return {
            "success": True,
            "token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }

    async def send_otp(self, email: str, method: str) -> Dict[str, Any]:
        """Send OTP for login"""
        # Generate OTP
        otp_code = generate_otp()

        # Create OTP record
        otp = OTPCode(
            email=email,
            code=otp_code,
            method=method,
            purpose="login",
            expires_at=get_otp_expiry_time(),
        )
        self.session.add(otp)
        await self.session.commit()

        # Send OTP
        if method == "email":
            await ses_service.send_otp_email(email, otp_code, "inicio de sesión")
        elif method == "sms":
            # Get user phone
            result = await self.session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user and user.telefono:
                await sns_service.send_otp_sms(user.telefono, otp_code)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No phone number registered",
                )

        return {
            "success": True,
            "message": f"Verification code sent via {method}",
        }

    async def verify_otp(self, email: str, otp_code: str) -> Dict[str, Any]:
        """Verify OTP and login"""
        # Get OTP
        result = await self.session.execute(
            select(OTPCode).where(
                OTPCode.email == email,
                OTPCode.code == otp_code,
                OTPCode.is_used == False,
            )
        )
        otp = result.scalar_one_or_none()

        if not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        # Check if expired
        if is_expired(otp.expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code expired",
            )

        # Get user
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Mark OTP as used
        otp.is_used = True
        otp.used_at = datetime.utcnow()

        # Update last login
        user.last_login = datetime.utcnow()
        await self.session.commit()

        # Generate tokens
        tokens = create_token_pair(user.id)

        return {
            "success": True,
            "token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }

    async def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> Dict[str, Any]:
        """Change user password"""
        # Get user
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Update password
        user.password_hash = hash_password(new_password)
        await self.session.commit()

        return {
            "success": True,
            "message": "Password changed successfully",
        }

    async def send_reset_code(self, email: str) -> Dict[str, Any]:
        """Send password reset code"""
        # Check if user exists
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            # Don't reveal if email exists
            return {
                "success": True,
                "message": "If the email exists, a reset code has been sent",
            }

        # Generate OTP
        otp_code = generate_otp()

        # Create OTP record
        otp = OTPCode(
            email=email,
            code=otp_code,
            method="email",
            purpose="password_reset",
            expires_at=get_otp_expiry_time(),
        )
        self.session.add(otp)
        await self.session.commit()

        # Send reset email
        await ses_service.send_password_reset_email(email, otp_code)

        return {
            "success": True,
            "message": "If the email exists, a reset code has been sent",
        }

    async def validate_user_organization(
        self, user_id: int, organization_id: int
    ) -> Dict[str, Any]:
        """Check if user belongs to organization"""
        result = await self.session.execute(
            select(UserOrganization).where(
                UserOrganization.user_id == user_id,
                UserOrganization.organization_id == organization_id,
            )
        )
        membership = result.scalar_one_or_none()

        if membership:
            return {"valid": True, "message": "User belongs to organization"}
        else:
            return {"valid": False, "message": "User does not belong to organization"}

    async def register_user_organization(
        self, user_id: int, organization_id: int
    ) -> Dict[str, Any]:
        """Register user to organization"""
        # Check if already registered
        result = await self.session.execute(
            select(UserOrganization).where(
                UserOrganization.user_id == user_id,
                UserOrganization.organization_id == organization_id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered to this organization",
            )

        # Create membership
        membership = UserOrganization(
            user_id=user_id,
            organization_id=organization_id,
        )
        self.session.add(membership)
        await self.session.commit()

        return {"success": True}
