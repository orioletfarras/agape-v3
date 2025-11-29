"""User profile schemas"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# Profile
class UserProfileResponse(BaseModel):
    id: int
    username: Optional[str]
    email: str
    nombre: Optional[str]
    apellidos: Optional[str]
    profile_image_url: Optional[str]
    bio: Optional[str]
    onboarding_completed: bool
    role: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UpdatePersonalInfoRequest(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)


class UpdatePersonalInfoResponse(BaseModel):
    success: bool = True


class GetPersonalInfoResponse(BaseModel):
    nombre: Optional[str]
    apellidos: Optional[str]
    email: str
    fecha_nacimiento: Optional[datetime]
    genero: Optional[str]
    telefono: Optional[str]


# Profile Image
class UploadProfileImageResponse(BaseModel):
    success: bool = True
    image_url: str


# User Settings
class UpdateUserSettingRequest(BaseModel):
    key: str = Field(..., max_length=100)
    value: str


class UpdateUserSettingResponse(BaseModel):
    success: bool = True


# Nickname/Username
class CheckNicknameRequest(BaseModel):
    nickname: str = Field(..., min_length=3, max_length=50)


class CheckNicknameResponse(BaseModel):
    available: bool


class CompleteProfileRequest(BaseModel):
    nickname: str = Field(..., min_length=3, max_length=50)
    parish_id: Optional[int] = None


class CompleteProfileResponse(BaseModel):
    success: bool = True


# Organization
class OrganizationBasic(BaseModel):
    id: int
    name: str
    image_url: Optional[str]

    class Config:
        from_attributes = True


class PrimaryOrganizationResponse(OrganizationBasic):
    pass


class UpdatePrimaryOrganizationRequest(BaseModel):
    organization_id: int


class UpdatePrimaryOrganizationResponse(BaseModel):
    success: bool = True


# Current User
class CurrentUserResponse(BaseModel):
    id: int
    username: Optional[str]
    email: str

    class Config:
        from_attributes = True
