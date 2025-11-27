"""Messaging endpoints"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.messaging_service import MessagingService
from app.domain.schemas.messaging import (
    CreateConversationRequest,
    SendMessageRequest,
    UpdateMessageRequest,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    MessageListResponse,
    MessageSendResponse,
    MessageDeleteResponse,
    ConversationReadResponse
)

router = APIRouter(tags=["Messaging"], prefix="/messaging")


# Dependency
async def get_messaging_service(session: AsyncSession = Depends(get_db)) -> MessagingService:
    return MessagingService(session)


# ============================================================
# CONVERSATION ENDPOINTS
# ============================================================

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Create or get existing direct conversation with a user

    **Requirements:**
    - Must be authenticated
    - Creates new conversation or returns existing one
    """
    return await messaging_service.create_direct_conversation(
        user1_id=current_user.id,
        user2_id=data.user_id
    )


@router.get("/conversations", response_model=ConversationListResponse, status_code=status.HTTP_200_OK)
async def get_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Get user's conversations

    Returns paginated list of conversations with last message and unread count
    """
    return await messaging_service.get_user_conversations(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Get conversation by ID

    **Requirements:**
    - User must be a participant in the conversation
    """
    return await messaging_service.get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )


@router.delete("/conversations/{conversation_id}", response_model=MessageDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Delete a conversation

    **Requirements:**
    - User must be a participant in the conversation
    """
    return await messaging_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )


@router.patch("/conversations/{conversation_id}/read", response_model=ConversationReadResponse, status_code=status.HTTP_200_OK)
async def mark_conversation_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Mark conversation as read

    Resets unread count to 0 for the current user
    """
    return await messaging_service.mark_conversation_read(
        conversation_id=conversation_id,
        user_id=current_user.id
    )


# ============================================================
# MESSAGE ENDPOINTS
# ============================================================

@router.post("/messages", response_model=MessageSendResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Send a message in a conversation

    **Requirements:**
    - User must be a participant in the conversation
    - Increments unread count for other participants
    """
    return await messaging_service.send_message(
        conversation_id=data.conversation_id,
        sender_id=current_user.id,
        content=data.content,
        reply_to_message_id=data.reply_to_message_id
    )


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse, status_code=status.HTTP_200_OK)
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Get messages for a conversation

    Returns paginated list of messages (newest first)

    **Requirements:**
    - User must be a participant in the conversation
    """
    return await messaging_service.get_conversation_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )


@router.put("/messages/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def update_message(
    message_id: int,
    data: UpdateMessageRequest,
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Update a message

    **Requirements:**
    - Only the message sender can update it
    """
    return await messaging_service.update_message(
        message_id=message_id,
        user_id=current_user.id,
        content=data.content
    )


@router.delete("/messages/{message_id}", response_model=MessageDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    messaging_service: MessagingService = Depends(get_messaging_service)
):
    """
    Delete a message (soft delete)

    **Requirements:**
    - Only the message sender can delete it
    """
    return await messaging_service.delete_message(
        message_id=message_id,
        user_id=current_user.id
    )
