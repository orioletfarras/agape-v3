"""Authentication endpoints"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.application.services.auth_service import AuthService
from app.application.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterStartRequest,
    RegisterStartResponse,
    RegisterVerifyEmailRequest,
    RegisterVerifyEmailResponse,
    RegisterCompleteRequest,
    RegisterCompleteResponse,
    RegisterResendRequest,
    RegisterResendResponse,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    SendResetCodeRequest,
    SendResetCodeResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ValidateTokenResponse,
    ValidateUserOrganizationRequest,
    ValidateUserOrganizationResponse,
    RegisterUserOrganizationRequest,
    RegisterUserOrganizationResponse,
)
from app.api.dependencies import get_current_user
from app.infrastructure.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService"""
    return AuthService(session)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login with email and password

    Returns JWT access token and refresh token
    """
    return await auth_service.login(data.email, data.password)


@router.post("/register-start", response_model=RegisterStartResponse, status_code=status.HTTP_200_OK)
async def register_start(
    data: RegisterStartRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Start registration process

    Creates a registration session and sends verification email
    """
    return await auth_service.register_start(data.email, data.password)


@router.post("/register-verify-email", response_model=RegisterVerifyEmailResponse, status_code=status.HTTP_200_OK)
async def register_verify_email(
    data: RegisterVerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Verify email with OTP code

    Marks email as verified in the registration session
    """
    return await auth_service.register_verify_email(data.registration_id, data.code)


@router.post("/register-complete", response_model=RegisterCompleteResponse, status_code=status.HTTP_200_OK)
async def register_complete(
    data: RegisterCompleteRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Complete registration

    Creates the user account and returns JWT tokens
    """
    return await auth_service.register_complete(
        data.registration_id,
        data.username,
        data.name,
    )


@router.post("/register-resend-email", response_model=RegisterResendResponse, status_code=status.HTTP_200_OK)
async def register_resend_email(
    data: RegisterResendRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Resend verification email

    Generates a new OTP and sends it via email
    """
    # Get registration session to get email
    from app.infrastructure.database.models import RegistrationSession
    from sqlalchemy import select

    session = auth_service.session
    result = await session.execute(
        select(RegistrationSession).where(
            RegistrationSession.registration_id == data.registration_id
        )
    )
    reg_session = result.scalar_one_or_none()

    if not reg_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration session not found",
        )

    # Resend OTP via email
    return await auth_service.send_otp(reg_session.email, "email")


@router.post("/register-resend-sms", response_model=RegisterResendResponse, status_code=status.HTTP_200_OK)
async def register_resend_sms(
    data: RegisterResendRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Resend verification SMS

    Generates a new OTP and sends it via SMS
    """
    # Get registration session to get email/phone
    from app.infrastructure.database.models import RegistrationSession
    from sqlalchemy import select

    session = auth_service.session
    result = await session.execute(
        select(RegistrationSession).where(
            RegistrationSession.registration_id == data.registration_id
        )
    )
    reg_session = result.scalar_one_or_none()

    if not reg_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration session not found",
        )

    # Resend OTP via SMS
    return await auth_service.send_otp(reg_session.email, "sms")


@router.post("/send-login-otp", response_model=SendOTPResponse, status_code=status.HTTP_200_OK)
async def send_login_otp(
    data: SendOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Send OTP for login

    Generates and sends a one-time password via email or SMS
    """
    return await auth_service.send_otp(data.email, data.method)


@router.post("/verify-otp", response_model=VerifyOTPResponse, status_code=status.HTTP_200_OK)
async def verify_otp(
    data: VerifyOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Verify OTP and login

    Validates the OTP code and returns JWT tokens
    """
    return await auth_service.verify_otp(data.email, data.otp)


@router.post("/change-password", response_model=ChangePasswordResponse, status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Change user password

    Requires authentication. Updates the user's password.
    """
    return await auth_service.change_password(
        current_user.id,
        data.current_password,
        data.new_password,
    )


@router.post("/send-reset-code", response_model=SendResetCodeResponse, status_code=status.HTTP_200_OK)
async def send_reset_code(
    data: SendResetCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Send password reset code

    Generates and sends a reset code via email
    """
    return await auth_service.send_reset_code(data.email)


@router.get("/validate-token", response_model=ValidateTokenResponse, status_code=status.HTTP_200_OK)
async def validate_token(
    current_user: User = Depends(get_current_user),
):
    """
    Validate JWT token

    Returns user_id if token is valid
    """
    return {
        "valid": True,
        "user_id": current_user.id,
    }


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token

    Takes a refresh token and returns a new access token
    """
    from app.infrastructure.security import verify_token, create_token_pair
    from app.infrastructure.database.models import RefreshToken as RefreshTokenModel
    from sqlalchemy import select

    # Verify refresh token
    payload = verify_token(data.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")

    # Check if refresh token exists in database
    session = auth_service.session
    result = await session.execute(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token == data.refresh_token,
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.is_revoked == False,
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    # Generate new token pair
    tokens = create_token_pair(user_id)

    # Revoke old refresh token
    token_record.is_revoked = True

    # Create new refresh token record
    from app.infrastructure.security import get_registration_expiry_time
    from datetime import datetime

    new_refresh_token = RefreshTokenModel(
        user_id=user_id,
        token=tokens["refresh_token"],
        expires_at=datetime.utcnow() + get_registration_expiry_time(),
    )
    session.add(new_refresh_token)
    await session.commit()

    return {
        "success": True,
        "token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout user

    Revokes all refresh tokens for the current user
    """
    from app.infrastructure.database.models import RefreshToken as RefreshTokenModel
    from sqlalchemy import update

    session = auth_service.session
    await session.execute(
        update(RefreshTokenModel)
        .where(
            RefreshTokenModel.user_id == current_user.id,
            RefreshTokenModel.is_revoked == False,
        )
        .values(is_revoked=True)
    )
    await session.commit()

    return {"success": True, "message": "Logged out successfully"}


@router.post("/validate-user-organization", response_model=ValidateUserOrganizationResponse, status_code=status.HTTP_200_OK)
async def validate_user_organization(
    data: ValidateUserOrganizationRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Check if user belongs to organization

    Returns validation status
    """
    return await auth_service.validate_user_organization(
        current_user.id,
        data.organization_id,
    )


@router.post("/register-user-organization", response_model=RegisterUserOrganizationResponse, status_code=status.HTTP_200_OK)
async def register_user_organization(
    data: RegisterUserOrganizationRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register user to organization

    Creates membership between user and organization
    """
    return await auth_service.register_user_organization(
        current_user.id,
        data.organization_id,
    )
