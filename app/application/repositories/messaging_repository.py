"""Messaging repository - Database operations"""
from typing import Tuple, List, Optional
from datetime import datetime
from sqlalchemy import select, func, and_, or_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    Conversation, ConversationParticipant, Message, User
)


class MessagingRepository:
    """Repository for messaging data operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # CONVERSATION OPERATIONS
    # ============================================================

    async def create_conversation(
        self,
        conversation_type: str,
        channel_id: Optional[int] = None,
        title: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            type=conversation_type,
            channel_id=channel_id,
            title=title,
            image_url=image_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Get conversation by ID"""
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.participants))
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def find_direct_conversation(self, user1_id: int, user2_id: int) -> Optional[Conversation]:
        """Find existing direct conversation between two users"""
        # Get all direct conversations for user1
        result = await self.session.execute(
            select(Conversation)
            .join(ConversationParticipant, Conversation.id == ConversationParticipant.conversation_id)
            .where(
                and_(
                    Conversation.type == "direct",
                    ConversationParticipant.user_id == user1_id
                )
            )
        )
        conversations = result.scalars().all()

        # Check which ones have user2
        for conv in conversations:
            participants_result = await self.session.execute(
                select(ConversationParticipant)
                .where(ConversationParticipant.conversation_id == conv.id)
            )
            participants = participants_result.scalars().all()
            participant_ids = {p.user_id for p in participants}

            if user2_id in participant_ids and len(participant_ids) == 2:
                return conv

        return None

    async def get_user_conversations(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Conversation], int]:
        """Get user's conversations with pagination"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(Conversation.id))
            .join(ConversationParticipant, Conversation.id == ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # Get conversations
        query = (
            select(Conversation)
            .join(ConversationParticipant, Conversation.id == ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        conversations = result.scalars().all()

        return list(conversations), total

    async def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation"""
        result = await self.session.execute(
            delete(Conversation).where(Conversation.id == conversation_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    # ============================================================
    # PARTICIPANT OPERATIONS
    # ============================================================

    async def add_participant(
        self,
        conversation_id: int,
        user_id: int
    ) -> ConversationParticipant:
        """Add participant to conversation"""
        participant = ConversationParticipant(
            conversation_id=conversation_id,
            user_id=user_id,
            last_read_at=datetime.utcnow(),
            unread_count=0,
            joined_at=datetime.utcnow()
        )
        self.session.add(participant)
        await self.session.commit()
        await self.session.refresh(participant)
        return participant

    async def get_participant(
        self,
        conversation_id: int,
        user_id: int
    ) -> Optional[ConversationParticipant]:
        """Get conversation participant"""
        result = await self.session.execute(
            select(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_conversation_participants(
        self,
        conversation_id: int
    ) -> List[ConversationParticipant]:
        """Get all participants of a conversation"""
        result = await self.session.execute(
            select(ConversationParticipant)
            .options(selectinload(ConversationParticipant.user))
            .where(ConversationParticipant.conversation_id == conversation_id)
        )
        return list(result.scalars().all())

    async def mark_conversation_read(
        self,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """Mark conversation as read for user"""
        result = await self.session.execute(
            update(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id
                )
            )
            .values(
                last_read_at=datetime.utcnow(),
                unread_count=0
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def increment_unread_count(
        self,
        conversation_id: int,
        user_id: int
    ) -> None:
        """Increment unread count for user in conversation"""
        await self.session.execute(
            update(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id
                )
            )
            .values(
                unread_count=ConversationParticipant.unread_count + 1
            )
        )
        await self.session.commit()

    # ============================================================
    # MESSAGE OPERATIONS
    # ============================================================

    async def create_message(
        self,
        conversation_id: int,
        sender_id: int,
        content: str,
        reply_to_message_id: Optional[int] = None,
        message_type: str = "text"
    ) -> Message:
        """Create a new message"""
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            reply_to_message_id=reply_to_message_id,
            is_deleted=False,
            created_at=datetime.utcnow()
        )
        self.session.add(message)

        # Update conversation updated_at
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=datetime.utcnow())
        )

        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by ID"""
        result = await self.session.execute(
            select(Message)
            .options(selectinload(Message.sender))
            .where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_conversation_messages(
        self,
        conversation_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Message], int]:
        """Get messages for a conversation with pagination"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.is_deleted == False
                )
            )
        )
        total = count_result.scalar() or 0

        # Get messages (newest first)
        query = (
            select(Message)
            .options(selectinload(Message.sender))
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.is_deleted == False
                )
            )
            .order_by(Message.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        messages = result.scalars().all()

        return list(messages), total

    async def get_last_message(self, conversation_id: int) -> Optional[Message]:
        """Get last message in conversation"""
        result = await self.session.execute(
            select(Message)
            .options(selectinload(Message.sender))
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.is_deleted == False
                )
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_message(
        self,
        message_id: int,
        content: str
    ) -> Optional[Message]:
        """Update message content"""
        await self.session.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(
                content=content,
                edited_at=datetime.utcnow()
            )
        )
        await self.session.commit()

        # Return updated message
        return await self.get_message_by_id(message_id)

    async def delete_message(self, message_id: int) -> bool:
        """Soft delete a message"""
        result = await self.session.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(
                is_deleted=True,
                deleted_at=datetime.utcnow()
            )
        )
        await self.session.commit()
        return result.rowcount > 0
