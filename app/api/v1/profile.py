"""User profile endpoints"""
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.application.services.user_service import UserService
from app.domain.schemas import (
    UserProfileResponse,
    UpdatePersonalInfoRequest,
    UpdatePersonalInfoResponse,
    GetPersonalInfoResponse,
    UploadProfileImageResponse,
    UpdateUserSettingRequest,
    UpdateUserSettingResponse,
    CheckNicknameRequest,
    CheckNicknameResponse,
    CompleteProfileRequest,
    CompleteProfileResponse,
    PrimaryOrganizationResponse,
    UpdatePrimaryOrganizationRequest,
    UpdatePrimaryOrganizationResponse,
    CurrentUserResponse,
)
from app.api.dependencies import get_current_user
from app.infrastructure.database.models import User

router = APIRouter(tags=["Profile"])


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency to get UserService"""
    return UserService(session)


@router.get("/profile", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get current user profile

    Returns complete user profile information
    """
    user = await user_service.get_profile(current_user.id)
    return user


@router.post("/upload-profile-image", response_model=UploadProfileImageResponse, status_code=status.HTTP_200_OK)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Upload profile image

    Uploads image to S3 and updates user profile
    """
    return await user_service.upload_profile_image(current_user.id, file)


@router.post("/update-personal-info", response_model=UpdatePersonalInfoResponse, status_code=status.HTTP_200_OK)
async def update_personal_info(
    data: UpdatePersonalInfoRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update personal information

    Updates nombre, apellidos, and bio
    """
    return await user_service.update_personal_info(
        current_user.id,
        nombre=data.nombre,
        apellidos=data.apellidos,
        bio=data.bio,
    )


@router.get("/get-personal-info", response_model=GetPersonalInfoResponse, status_code=status.HTTP_200_OK)
async def get_personal_info(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get personal information

    Returns detailed personal information
    """
    return await user_service.get_personal_info(current_user.id)


@router.post("/update-user-setting", response_model=UpdateUserSettingResponse, status_code=status.HTTP_200_OK)
async def update_user_setting(
    data: UpdateUserSettingRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update user setting

    Creates or updates a user setting key-value pair
    """
    return await user_service.update_user_setting(
        current_user.id,
        data.key,
        data.value,
    )


@router.post("/check-nickname", response_model=CheckNicknameResponse, status_code=status.HTTP_200_OK)
async def check_nickname(
    data: CheckNicknameRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Check if nickname is available

    Returns availability status
    Allows user to use their own current nickname
    """
    return await user_service.check_nickname(data.nickname, current_user.id)


@router.post("/complete-profile", response_model=CompleteProfileResponse, status_code=status.HTTP_200_OK)
async def complete_profile(
    data: CompleteProfileRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Complete user profile (onboarding)

    Sets username and completes onboarding
    """
    return await user_service.complete_profile(
        current_user.id,
        data.nickname,
        data.organization_id,
    )


@router.get("/user/primary-organization", response_model=PrimaryOrganizationResponse, status_code=status.HTTP_200_OK)
async def get_primary_organization(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get user's primary organization

    Returns organization details
    """
    org = await user_service.get_primary_organization(current_user.id)

    if not org:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No primary organization set",
        )

    return org


@router.put("/user/primary-organization", response_model=UpdatePrimaryOrganizationResponse, status_code=status.HTTP_200_OK)
async def update_primary_organization(
    data: UpdatePrimaryOrganizationRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update user's primary organization

    Sets the primary organization for the user
    """
    return await user_service.update_primary_organization(
        current_user.id,
        data.organization_id,
    )


@router.get("/current_user", response_model=CurrentUserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user basic info

    Returns id, username, and email
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }
