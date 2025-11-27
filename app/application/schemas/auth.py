"""Authentication schemas"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


# Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    success: bool = True
    token: str
    refresh_token: str
    user: "UserBasicInfo"


# Register
class RegisterStartRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

    @validator("password")
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v


class RegisterStartResponse(BaseModel):
    success: bool = True
    message: str
    registration_id: str


class RegisterVerifyEmailRequest(BaseModel):
    registration_id: str
    code: str = Field(..., min_length=6, max_length=6)


class RegisterVerifyEmailResponse(BaseModel):
    success: bool = True
    message: str


class RegisterCompleteRequest(BaseModel):
    registration_id: str
    username: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)


class RegisterCompleteResponse(BaseModel):
    success: bool = True
    token: str
    refresh_token: str


class RegisterResendRequest(BaseModel):
    registration_id: str


class RegisterResendResponse(BaseModel):
    success: bool = True
    message: str


# OTP
class SendOTPRequest(BaseModel):
    email: EmailStr
    method: str = Field(..., pattern="^(email|sms)$")


class SendOTPResponse(BaseModel):
    success: bool = True
    message: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class VerifyOTPResponse(BaseModel):
    success: bool = True
    token: str
    refresh_token: str


# Password
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)

    @validator("new_password")
    def validate_new_password(cls, v, values):
        if "current_password" in values and v == values["current_password"]:
            raise ValueError("New password must be different from current password")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v


class ChangePasswordResponse(BaseModel):
    success: bool = True
    message: str


class SendResetCodeRequest(BaseModel):
    email: EmailStr


class SendResetCodeResponse(BaseModel):
    success: bool = True
    message: str


# Token
class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    success: bool = True
    token: str
    refresh_token: str


class ValidateTokenResponse(BaseModel):
    valid: bool = True
    user_id: int


# User Info (basic)
class UserBasicInfo(BaseModel):
    id: int
    email: str
    username: Optional[str]

    class Config:
        from_attributes = True


# Identity Verification
class CreateVerificationSessionResponse(BaseModel):
    success: bool = True
    session_id: str
    verification_url: str


class VerifyIdentityStatusResponse(BaseModel):
    status: str  # pending, verified, failed
    message: str


# Organization
class ValidateUserOrganizationRequest(BaseModel):
    organization_id: int


class ValidateUserOrganizationResponse(BaseModel):
    valid: bool
    message: str


class RegisterUserOrganizationRequest(BaseModel):
    organization_id: int


class RegisterUserOrganizationResponse(BaseModel):
    success: bool = True
