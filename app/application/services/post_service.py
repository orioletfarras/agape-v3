"""Post business logic service"""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repositories.post_repository import PostRepository
from app.domain.schemas.post import (
    PostResponse, PostListResponse, PostStatsResponse,
    PostReactionResponse, PostDeleteResponse,
    PostAuthorResponse, PostChannelResponse, PostEventResponse
)
from app.infrastructure.database.models import User


class PostService:
    """Service for post business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PostRepository(session)

    async def create_post(
        self,
        user_id: int,
        channel_id: int,
        text: str,
        images: Optional[List[str]] = None,
        video_url: Optional[str] = None
    ) -> PostResponse:
        """
        Create a new post
        User must be subscribed to the channel to post
        """
        # Check if user can post in this channel
        can_post = await self.repo.check_user_can_post_in_channel(user_id, channel_id)
        if not can_post:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a channel admin or organization admin to post"
            )

        # Create post
        post = await self.repo.create_post(
            channel_id=channel_id,
            author_id=user_id,
            text=text,
            images=images,
            video_url=video_url
        )

        # Return full response
        return await self._build_post_response(post, user_id)

    async def get_post_by_id(self, post_id: int, user_id: int) -> PostResponse:
        """Get a single post by ID"""
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        return await self._build_post_response(post, user_id)

    async def get_posts_feed(
        self,
        user_id: int,
        channel_id: Optional[int] = None,
        author_id: Optional[int] = None,
        subscribed_only: bool = True,
        include_hidden: bool = False,
        only_favorites: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> PostListResponse:
        """
        Get posts feed for user
        By default, only returns posts from channels the user is subscribed to
        """
        # Get posts
        posts, total = await self.repo.get_posts_from_subscribed_channels(
            user_id=user_id,
            channel_id=channel_id,
            author_id=author_id,
            subscribed_only=subscribed_only,
            include_hidden=include_hidden,
            only_favorites=only_favorites,
            page=page,
            page_size=page_size
        )

        # Build response for each post
        post_responses = []
        for post in posts:
            post_response = await self._build_post_response(post, user_id)
            post_responses.append(post_response)

        # Calculate pagination
        has_more = (page * page_size) < total

        return PostListResponse(
            posts=post_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    async def update_post(
        self,
        post_id: int,
        user_id: int,
        user: User,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        video_url: Optional[str] = None,
        posttag: Optional[str] = None
    ) -> PostResponse:
        """
        Update a post.
        User must be:
        - Superadmin, OR
        - Channel admin, OR
        - Organization admin
        """
        # Get post
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        # Check permissions (superadmin, channel admin, or org admin)
        can_modify = await self.repo.check_user_can_manage_post(user_id, post.channel_id, user.role)
        if not can_modify:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a superadmin, channel admin, or organization admin to modify posts"
            )

        # Update post
        updated_post = await self.repo.update_post(
            post_id=post_id,
            text=text,
            images=images,
            video_url=video_url,
            posttag=posttag
        )

        return await self._build_post_response(updated_post, user_id)

    async def delete_post(self, post_id: int, user_id: int, user: User) -> PostDeleteResponse:
        """
        Delete a post.
        User must be:
        - Superadmin, OR
        - Channel admin, OR
        - Organization admin
        """
        # Get post
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        # Check permissions (superadmin, channel admin, or org admin)
        can_modify = await self.repo.check_user_can_manage_post(user_id, post.channel_id, user.role)
        if not can_modify:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a superadmin, channel admin, or organization admin to delete posts"
            )

        # Delete post
        success = await self.repo.delete_post(post_id)

        return PostDeleteResponse(
            success=success,
            message="Post deleted successfully" if success else "Failed to delete post"
        )

    # ============================================================
    # REACTIONS
    # ============================================================

    async def toggle_like(self, post_id: int, user_id: int, action: str) -> PostReactionResponse:
        """Toggle like on a post"""
        # Check post exists
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        if action == "like":
            success = await self.repo.add_like(post_id, user_id)

            # If user already liked, return 200 with already_liked flag
            if not success:
                current_count = await self.repo.get_likes_count(post_id)
                return PostReactionResponse(
                    success=True,
                    action=action,
                    new_count=current_count,
                    already_liked=True
                )
        elif action == "unlike":
            success = await self.repo.remove_like(post_id, user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You haven't liked this post"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action"
            )

        # Get new count
        new_count = await self.repo.get_likes_count(post_id)

        return PostReactionResponse(
            success=True,
            action=action,
            new_count=new_count,
            already_liked=False
        )

    async def toggle_pray(self, post_id: int, user_id: int, action: str) -> PostReactionResponse:
        """Toggle pray on a post"""
        # Check post exists
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        if action == "pray":
            success = await self.repo.add_pray(post_id, user_id)

            # If user already prayed, return 200 with already_prayed flag
            if not success:
                current_count = await self.repo.get_prays_count(post_id)
                return PostReactionResponse(
                    success=True,
                    action=action,
                    new_count=current_count,
                    already_prayed=True
                )
        elif action == "unpray":
            success = await self.repo.remove_pray(post_id, user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You haven't prayed for this post"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action"
            )

        # Get new count
        new_count = await self.repo.get_prays_count(post_id)

        return PostReactionResponse(
            success=True,
            action=action,
            new_count=new_count,
            already_prayed=False
        )

    async def toggle_favorite(self, post_id: int, user_id: int, action: str) -> PostReactionResponse:
        """Toggle favorite on a post"""
        # Check post exists
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        if action == "favorite":
            success = await self.repo.add_favorite(post_id, user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This post is already in your favorites"
                )
        elif action == "unfavorite":
            success = await self.repo.remove_favorite(post_id, user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This post is not in your favorites"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action"
            )

        # Get new count
        new_count = await self.repo.get_favorites_count(post_id)

        return PostReactionResponse(
            success=True,
            action=action,
            new_count=new_count
        )

    async def hide_post(self, post_id: int, user_id: int) -> dict:
        """Hide a post for the user"""
        # Check post exists
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        success = await self.repo.hide_post(post_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Post is already hidden"
            )

        return {"success": True, "message": "Post hidden successfully"}

    async def unhide_post(self, post_id: int, user_id: int) -> dict:
        """Unhide a post for the user"""
        success = await self.repo.unhide_post(post_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Post is not hidden"
            )

        return {"success": True, "message": "Post unhidden successfully"}

    async def get_post_stats(self, post_id: int) -> PostStatsResponse:
        """Get statistics for a post"""
        # Check post exists
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        likes_count = await self.repo.get_likes_count(post_id)
        prays_count = await self.repo.get_prays_count(post_id)
        favorites_count = await self.repo.get_favorites_count(post_id)

        return PostStatsResponse(
            like_count=likes_count,
            pray_count=prays_count,
            favorite_count=favorites_count,
            comment_count=0  # Will be implemented with comments module
        )

    async def get_user_favorites(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> PostListResponse:
        """Get user's favorite posts"""
        posts, total = await self.repo.get_user_favorites(user_id, page, page_size)

        # Build response for each post
        post_responses = []
        for post in posts:
            post_response = await self._build_post_response(post, user_id)
            post_responses.append(post_response)

        # Calculate pagination
        has_more = (page * page_size) < total

        return PostListResponse(
            posts=post_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _build_post_response(self, post, user_id: int) -> PostResponse:
        """Build complete post response with all related data"""
        # Get counts
        likes_count = await self.repo.get_likes_count(post.id)
        prays_count = await self.repo.get_prays_count(post.id)
        favorites_count = await self.repo.get_favorites_count(post.id)

        # Get user reactions
        is_liked = await self.repo.is_liked_by_user(post.id, user_id)
        is_prayed = await self.repo.is_prayed_by_user(post.id, user_id)
        is_favorited = await self.repo.is_favorited_by_user(post.id, user_id)
        is_hidden = await self.repo.is_hidden_by_user(post.id, user_id)

        # Build author response
        author = None
        if post.author:
            author = PostAuthorResponse(
                id=post.author.id,
                username=post.author.username,
                nombre=post.author.nombre,
                apellidos=post.author.apellidos,
                profile_image_url=post.author.profile_image_url
            )

        # Build channel response
        channel = None
        if post.channel:
            channel = PostChannelResponse(
                id=post.channel.id,
                name=post.channel.name,
                image_url=post.channel.image_url
            )

        return PostResponse(
            id=post.id,
            channel_id=post.channel_id,
            author_id=post.author_id,
            text=post.text,
            images=post.images,
            video_url=post.video_url,
            created_at=post.created_at,
            updated_at=post.updated_at,
            like_count=likes_count,
            pray_count=prays_count,
            favorite_count=favorites_count,
            comment_count=0,  # Will be implemented with comments module
            is_liked=is_liked,
            is_prayed=is_prayed,
            is_favorited=is_favorited,
            is_hidden=is_hidden,
            author=author,
            channel=channel
        )

    # ============================================================
    # POST MODERATION OPERATIONS
    # ============================================================

    async def publish_post(self, post_id: int) -> dict:
        """Publish a post"""
        success = await self.repo.publish_post(post_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        return {"success": True}

    async def unpublish_post(self, post_id: int) -> dict:
        """Unpublish a post"""
        success = await self.repo.unpublish_post(post_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        return {"success": True}

    async def mark_post_reviewed(self, post_id: int) -> dict:
        """Mark post as reviewed"""
        success = await self.repo.mark_post_reviewed(post_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        return {"success": True}

    async def mark_post_suspect(self, post_id: int) -> dict:
        """Mark post as suspect/reported"""
        success = await self.repo.mark_post_suspect(post_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        return {"success": True}

    async def get_post_prays_extended(self, id_code: str) -> dict:
        """Get extended pray information with user details"""
        # Get post by id_code
        post = await self.repo.get_post_by_id_code(id_code)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        prays = await self.repo.get_post_prays_extended(post.id)

        # Format dates as "hace X tiempo"
        from datetime import datetime, timedelta
        formatted_prays = []
        for pray in prays:
            time_diff = datetime.utcnow() - pray["created_at"]
            if time_diff < timedelta(hours=1):
                time_str = f"hace {int(time_diff.total_seconds() // 60)} min"
            elif time_diff < timedelta(days=1):
                time_str = f"hace {int(time_diff.total_seconds() // 3600)} h"
            else:
                time_str = f"hace {time_diff.days} días"

            formatted_prays.append({
                "user_id": pray["user_id"],
                "username": pray["username"],
                "profile_image_url": pray["profile_image_url"],
                "created_at": time_str
            })

        return {"prays": formatted_prays}
