"""Post repository for database operations"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    Post, PostLike, PostPray, PostFavorite, HiddenPost,
    User, Channel, Event, ChannelSubscription
)


class PostRepository:
    """Repository for post-related database operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_post(
        self,
        channel_id: int,
        author_id: int,
        text: str,
        images: Optional[List[str]] = None,
        video_url: Optional[str] = None
    ) -> Post:
        """Create a new post"""
        from app.infrastructure.aws.s3_service import s3_service

        post = Post(
            channel_id=channel_id,
            author_id=author_id,
            text=text,
            images=images,
            video_url=video_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post, ['author', 'channel'])

        # Reorganize images from temp location to final structure if images exist
        if images and len(images) > 0:
            final_image_urls = await s3_service.reorganize_post_images(post.id_code, images)
            post.images = final_image_urls
            await self.session.commit()
            await self.session.refresh(post, ['author', 'channel'])

        return post

    async def get_post_by_id(self, post_id: int) -> Optional[Post]:
        """Get post by ID with related data"""
        result = await self.session.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.channel)
            )
            .where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    async def get_posts_from_subscribed_channels(
        self,
        user_id: int,
        channel_id: Optional[int] = None,
        author_id: Optional[int] = None,
        subscribed_only: bool = True,
        include_hidden: bool = False,
        only_favorites: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Post], int]:
        """
        Get posts feed for user
        Returns (posts, total_count)
        """
        # Base query
        query = select(Post).options(
            selectinload(Post.author),
            selectinload(Post.channel)
        )

        # Filter by subscribed channels only
        if subscribed_only:
            query = query.join(
                ChannelSubscription,
                ChannelSubscription.channel_id == Post.channel_id
            ).where(ChannelSubscription.user_id == user_id)

        # Apply filters
        if channel_id:
            query = query.where(Post.channel_id == channel_id)

        if author_id:
            query = query.where(Post.author_id == author_id)

        # Filter hidden posts
        if not include_hidden:
            hidden_subquery = (
                select(HiddenPost.post_id)
                .where(HiddenPost.user_id == user_id)
            )
            query = query.where(~Post.id.in_(hidden_subquery))

        # Filter favorites only
        if only_favorites:
            query = query.join(PostFavorite, PostFavorite.post_id == Post.id).where(
                PostFavorite.user_id == user_id
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Post.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.session.execute(query)
        posts = result.scalars().all()

        return list(posts), total

    async def update_post(
        self,
        post_id: int,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        video_url: Optional[str] = None
    ) -> Optional[Post]:
        """Update a post"""
        post = await self.get_post_by_id(post_id)
        if not post:
            return None

        if text is not None:
            post.text = text
        if images is not None:
            post.images = images
        if video_url is not None:
            post.video_url = video_url

        post.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def delete_post(self, post_id: int) -> bool:
        """Delete a post"""
        post = await self.get_post_by_id(post_id)
        if not post:
            return False

        await self.session.delete(post)
        await self.session.commit()
        return True

    # ============================================================
    # REACTIONS
    # ============================================================

    async def add_like(self, post_id: int, user_id: int) -> bool:
        """Add a like to a post"""
        # Check if already liked
        existing = await self.session.execute(
            select(PostLike).where(
                and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
            )
        )
        if existing.scalar_one_or_none():
            return False

        like = PostLike(post_id=post_id, user_id=user_id, created_at=datetime.utcnow())
        self.session.add(like)
        await self.session.commit()
        return True

    async def remove_like(self, post_id: int, user_id: int) -> bool:
        """Remove a like from a post"""
        result = await self.session.execute(
            delete(PostLike).where(
                and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def add_pray(self, post_id: int, user_id: int) -> bool:
        """Add a pray to a post"""
        existing = await self.session.execute(
            select(PostPray).where(
                and_(PostPray.post_id == post_id, PostPray.user_id == user_id)
            )
        )
        if existing.scalar_one_or_none():
            return False

        pray = PostPray(post_id=post_id, user_id=user_id, created_at=datetime.utcnow())
        self.session.add(pray)
        await self.session.commit()
        return True

    async def remove_pray(self, post_id: int, user_id: int) -> bool:
        """Remove a pray from a post"""
        result = await self.session.execute(
            delete(PostPray).where(
                and_(PostPray.post_id == post_id, PostPray.user_id == user_id)
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def add_favorite(self, post_id: int, user_id: int) -> bool:
        """Add a post to favorites"""
        existing = await self.session.execute(
            select(PostFavorite).where(
                and_(PostFavorite.post_id == post_id, PostFavorite.user_id == user_id)
            )
        )
        if existing.scalar_one_or_none():
            return False

        favorite = PostFavorite(post_id=post_id, user_id=user_id, created_at=datetime.utcnow())
        self.session.add(favorite)
        await self.session.commit()
        return True

    async def remove_favorite(self, post_id: int, user_id: int) -> bool:
        """Remove a post from favorites"""
        result = await self.session.execute(
            delete(PostFavorite).where(
                and_(PostFavorite.post_id == post_id, PostFavorite.user_id == user_id)
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def hide_post(self, post_id: int, user_id: int) -> bool:
        """Hide a post for a user"""
        existing = await self.session.execute(
            select(HiddenPost).where(
                and_(HiddenPost.post_id == post_id, HiddenPost.user_id == user_id)
            )
        )
        if existing.scalar_one_or_none():
            return False

        hidden = HiddenPost(post_id=post_id, user_id=user_id, created_at=datetime.utcnow())
        self.session.add(hidden)
        await self.session.commit()
        return True

    async def unhide_post(self, post_id: int, user_id: int) -> bool:
        """Unhide a post for a user"""
        result = await self.session.execute(
            delete(HiddenPost).where(
                and_(HiddenPost.post_id == post_id, HiddenPost.user_id == user_id)
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    # ============================================================
    # STATISTICS
    # ============================================================

    async def get_likes_count(self, post_id: int) -> int:
        """Get number of likes for a post"""
        result = await self.session.execute(
            select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
        )
        return result.scalar() or 0

    async def get_prays_count(self, post_id: int) -> int:
        """Get number of prays for a post"""
        result = await self.session.execute(
            select(func.count(PostPray.id)).where(PostPray.post_id == post_id)
        )
        return result.scalar() or 0

    async def get_favorites_count(self, post_id: int) -> int:
        """Get number of favorites for a post"""
        result = await self.session.execute(
            select(func.count(PostFavorite.id)).where(PostFavorite.post_id == post_id)
        )
        return result.scalar() or 0

    async def is_liked_by_user(self, post_id: int, user_id: int) -> bool:
        """Check if user liked the post"""
        result = await self.session.execute(
            select(PostLike).where(
                and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_prayed_by_user(self, post_id: int, user_id: int) -> bool:
        """Check if user prayed for the post"""
        result = await self.session.execute(
            select(PostPray).where(
                and_(PostPray.post_id == post_id, PostPray.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_favorited_by_user(self, post_id: int, user_id: int) -> bool:
        """Check if post is in user's favorites"""
        result = await self.session.execute(
            select(PostFavorite).where(
                and_(PostFavorite.post_id == post_id, PostFavorite.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_hidden_by_user(self, post_id: int, user_id: int) -> bool:
        """Check if post is hidden by user"""
        result = await self.session.execute(
            select(HiddenPost).where(
                and_(HiddenPost.post_id == post_id, HiddenPost.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_user_favorites(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Post], int]:
        """Get user's favorite posts"""
        # Count total
        count_result = await self.session.execute(
            select(func.count(PostFavorite.id)).where(PostFavorite.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # Get posts
        query = (
            select(Post)
            .join(PostFavorite, PostFavorite.post_id == Post.id)
            .where(PostFavorite.user_id == user_id)
            .options(
                selectinload(Post.author),
                selectinload(Post.channel)
            )
            .order_by(PostFavorite.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        posts = result.scalars().all()

        return list(posts), total

    async def check_user_can_post_in_channel(self, user_id: int, channel_id: int) -> bool:
        """
        Check if user can post in channel.
        User must be:
        - Channel admin (in channel_admins table), OR
        - Channel creator, OR
        - Organization admin (has UserOrganization with is_admin=True for the channel's organization)
        """
        from app.infrastructure.database.models import ChannelAdmin, UserOrganization, Organization

        # Get channel to check creator_id and organization_id
        channel_result = await self.session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        if not channel:
            return False

        # Check if user is channel creator
        if channel.creator_id == user_id:
            return True

        # Check if user is channel admin
        admin_result = await self.session.execute(
            select(ChannelAdmin).where(
                and_(
                    ChannelAdmin.user_id == user_id,
                    ChannelAdmin.channel_id == channel_id
                )
            )
        )
        if admin_result.scalar_one_or_none() is not None:
            return True

        # Check if user is organization admin (if channel has organization)
        if channel.organization_id:
            # For now, we'll check if user is member of the organization
            # TODO: Add is_admin field to UserOrganization table
            org_result = await self.session.execute(
                select(UserOrganization).where(
                    and_(
                        UserOrganization.user_id == user_id,
                        UserOrganization.organization_id == channel.organization_id
                    )
                )
            )
            if org_result.scalar_one_or_none() is not None:
                return True

        return False

    # ============================================================
    # POST MODERATION OPERATIONS
    # ============================================================

    async def publish_post(self, post_id: int) -> bool:
        """Publish a post"""
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            return False

        post.is_published = True
        post.updated_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def unpublish_post(self, post_id: int) -> bool:
        """Unpublish a post"""
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            return False

        post.is_published = False
        post.updated_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def mark_post_reviewed(self, post_id: int) -> bool:
        """Mark post as reviewed"""
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            return False

        post.is_reviewed = True
        post.updated_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def mark_post_suspect(self, post_id: int) -> bool:
        """Mark post as suspect"""
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            return False

        post.is_suspected = True
        post.updated_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def get_post_prays_extended(self, post_id: int) -> List[dict]:
        """Get extended pray information including users"""
        from app.infrastructure.database.models import User
        result = await self.session.execute(
            select(PostPray, User)
            .join(User, PostPray.user_id == User.id)
            .where(PostPray.post_id == post_id)
            .order_by(PostPray.created_at.desc())
        )

        prays = []
        for pray, user in result.all():
            prays.append({
                "user_id": user.id,
                "username": user.username,
                "profile_image_url": user.profile_image_url,
                "created_at": pray.created_at
            })

        return prays
