"""Messaging domain schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class CreateConversationRequest(BaseModel):
    """Request to create a direct conversation"""
    user_id: int = Field(..., description="User ID to start conversation with")


class SendMessageRequest(BaseModel):
    """Request to send a message"""
    conversation_id: int
    content: str = Field(..., min_length=1, max_length=5000)
    reply_to_message_id: Optional[int] = None


class UpdateMessageRequest(BaseModel):
    """Request to update a message"""
    content: str = Field(..., min_length=1, max_length=5000)


class MarkConversationReadRequest(BaseModel):
    """Request to mark conversation as read"""
    conversation_id: int


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class UserBasicResponse(BaseModel):
    """Basic user info"""
    id: int
    username: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    profile_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Message response"""
    id: int
    conversation_id: int
    sender_id: int
    content: str
    message_type: str
    reply_to_message_id: Optional[int] = None
    is_deleted: bool
    created_at: datetime
    edited_at: Optional[datetime] = None
    sender: Optional[UserBasicResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: int
    type: str
    title: Optional[str] = None
    image_url: Optional[str] = None
    channel_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    unread_count: int = 0
    last_message: Optional[MessageResponse] = None
    participants: List[UserBasicResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    """Paginated list of conversations"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class MessageListResponse(BaseModel):
    """Paginated list of messages"""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class MessageSendResponse(BaseModel):
    """Response for sending a message"""
    success: bool
    message: MessageResponse


class MessageDeleteResponse(BaseModel):
    """Response for deleting a message"""
    success: bool
    message: str


class ConversationReadResponse(BaseModel):
    """Response for marking conversation as read"""
    success: bool
    message: str
