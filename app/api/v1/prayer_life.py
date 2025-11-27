"""Prayer Life / Automatic Channels endpoints"""
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user, get_current_user_optional
from app.application.services.prayer_life_service import PrayerLifeService
from app.domain.schemas.prayer_life import (
    AutomaticChannelsResponse,
    SubscribeAutomaticChannelResponse,
    UpdateChannelOrderRequest,
    UpdateChannelOrderResponse,
    ToggleHideChannelRequest,
    ToggleHideChannelResponse,
    CreateAutomaticChannelRequest,
    CreateAutomaticChannelResponse,
    UpdateChannelMetadataRequest,
    UpdateChannelMetadataResponse,
    DeleteAutomaticChannelResponse,
    GenerateWebAccessResponse,
)

router = APIRouter(tags=["Prayer Life"], prefix="/prayer-life")


# Dependency
async def get_prayer_life_service(session: AsyncSession = Depends(get_db)) -> PrayerLifeService:
    return PrayerLifeService(session)


@router.get("/automatic-channels", response_model=AutomaticChannelsResponse, status_code=status.HTTP_200_OK)
async def get_automatic_channels(
    language: str = Query(default="es", description="Language code (es, en, etc.)"),
    current_user: User = Depends(get_current_user_optional),
    prayer_life_service: PrayerLifeService = Depends(get_prayer_life_service)
):
    """
    Get all automatic prayer channels organized by categories

    **Query params:**
    - `language`: Language code (default: es)

    **Response:**
    ```json
    {
      "categories": [
        {
          "id": "readings",
          "name": "Lecturas Diarias",
          "channels": [
            {
              "id": 1,
              "id_code": "auto_abc123",
              "name": "Primera Lectura",
              "description": "Lectura del Antiguo Testamento",
              "image_url": "https://...",
              "subscribed": true,
              "has_content": true,
              "content": {
                "title": "Libro de Isaías",
                "text": "En aquel tiempo...",
                "audio_url": "https://..."
              }
            }
          ]
        }
      ]
    }
    ```
    """
    user_id = current_user.id if current_user else None
    return await prayer_life_service.get_automatic_channels(language=language, user_id=user_id)


@router.post("/automatic-channels/{channelIdCode}/subscribe", response_model=SubscribeAutomaticChannelResponse, status_code=status.HTTP_200_OK)
async def subscribe_automatic_channel(
    channelIdCode: str = Path(..., description="Channel ID code"),
    current_user: User = Depends(get_current_user),
    prayer_life_service: PrayerLifeService = Depends(get_prayer_life_service)
):
    """
    Subscribe/unsubscribe to automatic channel (toggles)

    **Response:**
    ```json
    {
      "success": true,
      "subscribed": true
    }
    ```
    """
    return await prayer_life_service.subscribe_automatic_channel(channelIdCode, current_user.id)


@router.post("/automatic-channels/order", response_model=UpdateChannelOrderResponse, status_code=status.HTTP_200_OK)
async def update_channel_order(
    request: UpdateChannelOrderRequest,
    current_user: User = Depends(get_current_user),
    prayer_life_service: PrayerLifeService = Depends(get_prayer_life_service)
):
    """
    Update user's custom channel order

    **Request:**
    ```json
    {
      "channel_order": ["auto_abc", "auto_def", "auto_xyz"]
    }
    ```

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await prayer_life_service.update_channel_order(request, current_user.id)


@router.post("/automatic-channels/toggle-hide", response_model=ToggleHideChannelResponse, status_code=status.HTTP_200_OK)
async def toggle_hide_channel(
    request: ToggleHideChannelRequest,
    current_user: User = Depends(get_current_user),
    prayer_life_service: PrayerLifeService = Depends(get_prayer_life_service)
):
    """
    Toggle hide/unhide automatic channel

    **Request:**
    ```json
    {
      "channel_id_code": "auto_abc123"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "hidden": true
    }
    ```
    """
    return await prayer_life_service.toggle_hide_channel(request, current_user.id)


@router.post("/automatic-channels/create", response_model=CreateAutomaticChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_automatic_channel(
    request: CreateAutomaticChannelRequest,
    current_user: User = Depends(get_current_user),
    prayer_life_service: PrayerLifeService = Depends(get_prayer_life_service)
):
    """
    Create a new automatic channel (admin only)

    **Request:**
    ```json
    {
      "name": "Nueva Oración",
      "organization_id": 1,
      "category": "prayers",
      "language": "es"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "channel_id": 123,
      "id_code": "auto_abc123"
    }
    ```
    """
    return await prayer_life_service.create_automatic_channel(request, current_user.id)


@router.post("/automatic-channels/update-metadata", response_model=UpdateChannelMetadataResponse, status_code=status.HTTP_200_OK)
async def update_channel_metadata(
    request: UpdateChannelMetadataRequest,
    current_user: User = Depends(get_current_user),
    prayer_life_service: PrayerLifeService = Depends(get_prayer_life_service)
):
    """
    Update automatic channel metadata (admin only)

    **Request:**
    ```json
    {
      "channel_id": 123,
      "name": "Nuevo Nombre",
      "description": "Nueva descripción"
    }
    ```

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await prayer_life_service.update_channel_metadata(request)


@router.delete("/automatic-channels/{channelId}", response_model=DeleteAutomaticChannelResponse, status_code=status.HTTP_200_OK)
async def delete_automatic_channel(
    channelId: int = Path(..., description="Channel ID"),
    current_user: User = Depends(get_current_user),
    prayer_life_service: PrayerLifeService = Depends(get_prayer_life_service)
):
    """
    Delete an automatic channel (admin only)

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await prayer_life_service.delete_automatic_channel(channelId)


@router.post("/generate-web-access", response_model=GenerateWebAccessResponse, status_code=status.HTTP_200_OK)
async def generate_web_access(
    current_user: User = Depends(get_current_user),
    prayer_life_service: PrayerLifeService = Depends(get_prayer_life_service)
):
    """
    Generate temporary web access token for prayer life

    **Response:**
    ```json
    {
      "success": true,
      "web_url": "https://agape.penwin.cloud/prayer-life?token=abc123",
      "token": "abc123xyz",
      "expires_at": "2025-01-16T10:00:00"
    }
    ```
    """
    return await prayer_life_service.generate_web_access(current_user.id)
