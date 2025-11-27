"""Messaging business logic service"""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.messaging_repository import MessagingRepository
from app.domain.schemas.messaging import (
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    MessageListResponse,
    MessageSendResponse,
    MessageDeleteResponse,
    ConversationReadResponse,
    UserBasicResponse
)


class MessagingService:
    """Service for messaging business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MessagingRepository(session)

    async def create_direct_conversation(
        self,
        user1_id: int,
        user2_id: int
    ) -> ConversationResponse:
        """Create or get existing direct conversation between two users"""
        # Check if conversation already exists
        existing = await self.repo.find_direct_conversation(user1_id, user2_id)
        if existing:
            return await self._build_conversation_response(existing, user1_id)

        # Create new conversation
        conversation = await self.repo.create_conversation(conversation_type="direct")

        # Add both participants
        await self.repo.add_participant(conversation.id, user1_id)
        await self.repo.add_participant(conversation.id, user2_id)

        return await self._build_conversation_response(conversation, user1_id)

    async def get_user_conversations(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> ConversationListResponse:
        """Get user's conversations"""
        conversations, total = await self.repo.get_user_conversations(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        # Build responses
        conversation_responses = []
        for conv in conversations:
            conv_response = await self._build_conversation_response(conv, user_id)
            conversation_responses.append(conv_response)

        has_more = (page * page_size) < total

        return ConversationListResponse(
            conversations=conversation_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def get_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> ConversationResponse:
        """Get conversation by ID"""
        # Check conversation exists
        conversation = await self.repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Check user is participant
        participant = await self.repo.get_participant(conversation_id, user_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation"
            )

        return await self._build_conversation_response(conversation, user_id)

    async def send_message(
        self,
        conversation_id: int,
        sender_id: int,
        content: str,
        reply_to_message_id: Optional[int] = None
    ) -> MessageSendResponse:
        """Send a message in a conversation"""
        # Check conversation exists
        conversation = await self.repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Check user is participant
        participant = await self.repo.get_participant(conversation_id, sender_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation"
            )

        # Create message
        message = await self.repo.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            reply_to_message_id=reply_to_message_id
        )

        # Increment unread count for other participants
        participants = await self.repo.get_conversation_participants(conversation_id)
        for p in participants:
            if p.user_id != sender_id:
                await self.repo.increment_unread_count(conversation_id, p.user_id)

        message_response = await self._build_message_response(message)

        return MessageSendResponse(
            success=True,
            message=message_response
        )

    async def get_conversation_messages(
        self,
        conversation_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> MessageListResponse:
        """Get messages for a conversation"""
        # Check conversation exists and user is participant
        conversation = await self.repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        participant = await self.repo.get_participant(conversation_id, user_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation"
            )

        # Get messages
        messages, total = await self.repo.get_conversation_messages(
            conversation_id=conversation_id,
            page=page,
            page_size=page_size
        )

        # Build responses
        message_responses = []
        for message in messages:
            msg_response = await self._build_message_response(message)
            message_responses.append(msg_response)

        has_more = (page * page_size) < total

        return MessageListResponse(
            messages=message_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def update_message(
        self,
        message_id: int,
        user_id: int,
        content: str
    ) -> MessageResponse:
        """Update a message"""
        # Get message
        message = await self.repo.get_message_by_id(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Check ownership
        if message.sender_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own messages"
            )

        # Update message
        updated_message = await self.repo.update_message(message_id, content)

        return await self._build_message_response(updated_message)

    async def delete_message(
        self,
        message_id: int,
        user_id: int
    ) -> MessageDeleteResponse:
        """Delete a message"""
        # Get message
        message = await self.repo.get_message_by_id(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Check ownership
        if message.sender_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own messages"
            )

        # Delete message
        success = await self.repo.delete_message(message_id)

        return MessageDeleteResponse(
            success=success,
            message="Message deleted successfully" if success else "Failed to delete message"
        )

    async def mark_conversation_read(
        self,
        conversation_id: int,
        user_id: int
    ) -> ConversationReadResponse:
        """Mark conversation as read"""
        # Check conversation exists
        conversation = await self.repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Check user is participant
        participant = await self.repo.get_participant(conversation_id, user_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation"
            )

        # Mark as read
        success = await self.repo.mark_conversation_read(conversation_id, user_id)

        return ConversationReadResponse(
            success=success,
            message="Conversation marked as read" if success else "Failed to mark conversation as read"
        )

    async def delete_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> MessageDeleteResponse:
        """Delete a conversation"""
        # Check conversation exists
        conversation = await self.repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Check user is participant
        participant = await self.repo.get_participant(conversation_id, user_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation"
            )

        # Delete conversation
        success = await self.repo.delete_conversation(conversation_id)

        return MessageDeleteResponse(
            success=success,
            message="Conversation deleted successfully" if success else "Failed to delete conversation"
        )

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _build_message_response(self, message) -> MessageResponse:
        """Build message response with sender info"""
        sender = None
        if message.sender:
            sender = UserBasicResponse(
                id=message.sender.id,
                username=message.sender.username,
                nombre=message.sender.nombre,
                apellidos=message.sender.apellidos,
                profile_image_url=message.sender.profile_image_url
            )

        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type,
            reply_to_message_id=message.reply_to_message_id,
            is_deleted=message.is_deleted,
            created_at=message.created_at,
            edited_at=message.edited_at,
            sender=sender
        )

    async def _build_conversation_response(
        self,
        conversation,
        current_user_id: int
    ) -> ConversationResponse:
        """Build conversation response with participants and last message"""
        # Get participants
        participants = await self.repo.get_conversation_participants(conversation.id)
        participant_responses = []
        unread_count = 0

        for p in participants:
            if p.user_id == current_user_id:
                unread_count = p.unread_count
            if p.user:
                participant_responses.append(
                    UserBasicResponse(
                        id=p.user.id,
                        username=p.user.username,
                        nombre=p.user.nombre,
                        apellidos=p.user.apellidos,
                        profile_image_url=p.user.profile_image_url
                    )
                )

        # Get last message
        last_message = await self.repo.get_last_message(conversation.id)
        last_message_response = None
        if last_message:
            last_message_response = await self._build_message_response(last_message)

        return ConversationResponse(
            id=conversation.id,
            type=conversation.type,
            title=conversation.title,
            image_url=conversation.image_url,
            channel_id=conversation.channel_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            unread_count=unread_count,
            last_message=last_message_response,
            participants=participant_responses
        )
