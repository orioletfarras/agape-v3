"""Posts endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.post_service import PostService
from app.infrastructure.aws.s3_service import S3Service
from app.domain.schemas.post import (
    CreatePostRequest,
    UpdatePostRequest,
    PostReactionRequest,
    PostResponse,
    PostListResponse,
    PostStatsResponse,
    PostReactionResponse,
    PostDeleteResponse
)

router = APIRouter(tags=["Posts"], prefix="/posts")


# Dependency to get post service
async def get_post_service(session: AsyncSession = Depends(get_db)) -> PostService:
    return PostService(session)


# ============================================================
# POST CRUD ENDPOINTS
# ============================================================

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: CreatePostRequest,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Create a new post in a channel

    **Requirements:**
    - User must be subscribed to the channel
    - Content is required (max 10,000 characters)
    - Optional: images, videos, event_id
    """
    return await post_service.create_post(
        user_id=current_user.id,
        channel_id=data.channel_id,
        text=data.text,
        images=data.images,
        video_url=data.video_url
    )


@router.get("", response_model=PostListResponse, status_code=status.HTTP_200_OK)
async def get_posts_feed(
    channel_id: Optional[int] = Query(None, description="Filter by channel"),
    author_id: Optional[int] = Query(None, description="Filter by author"),
    subscribed_only: bool = Query(True, description="Only show posts from subscribed channels"),
    include_hidden: bool = Query(False, description="Include hidden posts"),
    only_favorites: bool = Query(False, description="Only show favorite posts"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get posts feed for authenticated user

    **Filters:**
    - channel_id: Show posts from specific channel
    - author_id: Show posts from specific user
    - subscribed_only: Only show posts from subscribed channels (default: true)
    - include_hidden: Include posts the user has hidden
    - only_favorites: Only show favorited posts
    - page: Pagination page number
    - page_size: Number of posts per page (max 100)
    """
    return await post_service.get_posts_feed(
        user_id=current_user.id,
        channel_id=channel_id,
        author_id=author_id,
        subscribed_only=subscribed_only,
        include_hidden=include_hidden,
        only_favorites=only_favorites,
        page=page,
        page_size=page_size
    )


@router.get("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get a single post by ID

    Returns complete post data including:
    - Post content, images, videos
    - Author information
    - Channel information
    - Related event (if applicable)
    - Reaction counts (likes, prays, favorites, comments)
    - Current user's reactions
    """
    return await post_service.get_post_by_id(post_id, current_user.id)


@router.put("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def update_post(
    post_id: int,
    data: UpdatePostRequest,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Update a post

    **Requirements:**
    - Only the post author can update it
    - Can update: content, images, videos
    - Cannot update: channel_id, author_id, event_id
    """
    return await post_service.update_post(
        post_id=post_id,
        user_id=current_user.id,
        text=data.text,
        images=data.images,
        video_url=data.video_url
    )


@router.delete("/{post_id}", response_model=PostDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Delete a post

    **Requirements:**
    - Only the post author can delete it
    - Deletes all related data (likes, prays, favorites, comments)
    """
    return await post_service.delete_post(post_id, current_user.id)


# ============================================================
# POST REACTIONS ENDPOINTS
# ============================================================

@router.patch("/{post_id}/like", response_model=PostReactionResponse, status_code=status.HTTP_200_OK)
async def toggle_like(
    post_id: int,
    data: PostReactionRequest,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Like or unlike a post

    **Actions:**
    - "like": Add like to post
    - "unlike": Remove like from post

    Returns updated like count
    """
    return await post_service.toggle_like(post_id, current_user.id, data.action)


@router.patch("/{post_id}/pray", response_model=PostReactionResponse, status_code=status.HTTP_200_OK)
async def toggle_pray(
    post_id: int,
    data: PostReactionRequest,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Pray or unpray for a post

    **Actions:**
    - "pray": Add pray to post
    - "unpray": Remove pray from post

    Returns updated pray count
    """
    return await post_service.toggle_pray(post_id, current_user.id, data.action)


@router.patch("/{post_id}/favorite", response_model=PostReactionResponse, status_code=status.HTTP_200_OK)
async def toggle_favorite(
    post_id: int,
    data: PostReactionRequest,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Add or remove post from favorites

    **Actions:**
    - "favorite": Add post to favorites
    - "unfavorite": Remove post from favorites

    Returns updated favorite count
    """
    return await post_service.toggle_favorite(post_id, current_user.id, data.action)


@router.post("/{post_id}/hide", status_code=status.HTTP_200_OK)
async def hide_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Hide a post from the user's feed

    Hidden posts won't appear in the feed unless include_hidden=true
    """
    return await post_service.hide_post(post_id, current_user.id)


@router.delete("/{post_id}/hide", status_code=status.HTTP_200_OK)
async def unhide_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Unhide a previously hidden post
    """
    return await post_service.unhide_post(post_id, current_user.id)


# ============================================================
# POST STATISTICS ENDPOINTS
# ============================================================

@router.get("/{post_id}/stats", response_model=PostStatsResponse, status_code=status.HTTP_200_OK)
async def get_post_stats(
    post_id: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get statistics for a post

    Returns:
    - likes_count: Number of likes
    - prays_count: Number of prays
    - favorites_count: Number of users who favorited
    - comments_count: Number of comments
    """
    return await post_service.get_post_stats(post_id)


# ============================================================
# USER FAVORITES ENDPOINTS
# ============================================================

@router.get("/favorites/list", response_model=PostListResponse, status_code=status.HTTP_200_OK)
async def get_user_favorites(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get user's favorite posts

    Returns paginated list of posts the user has marked as favorite
    """
    return await post_service.get_user_favorites(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )


# ============================================================
# IMAGE/VIDEO UPLOAD ENDPOINTS
# ============================================================

@router.post("/upload-image", status_code=status.HTTP_200_OK)
async def upload_post_image(
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Upload an image for a post

    **Requirements:**
    - Must be authenticated
    - Supported formats: JPEG, PNG, JPG, WEBP
    - Max file size: 10MB
    - Image will be optimized and resized

    **Returns:**
    - image_url: URL of the uploaded image on S3

    **Usage:**
    1. Upload image using this endpoint
    2. Use returned URL in CreatePostRequest.images array
    """
    s3_service = S3Service()

    # Read file data
    file_data = await file.read()

    # Upload to S3
    result = await s3_service.upload_post_image(current_user.id, file_data, file.filename)

    return {
        "success": True,
        "image_url": result["url"]
    }


@router.post("/upload-video", status_code=status.HTTP_200_OK)
async def upload_post_video(
    file: UploadFile = File(..., description="Video file to upload"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Upload a video for a post

    **Requirements:**
    - Must be authenticated
    - Supported formats: MP4, MOV, AVI
    - Max file size: 100MB

    **Returns:**
    - video_url: URL of the uploaded video on S3

    **Usage:**
    1. Upload video using this endpoint
    2. Use returned URL in CreatePostRequest.videos array
    """
    s3_service = S3Service()

    # Read file data
    file_data = await file.read()

    # Upload to S3
    result = await s3_service.upload_post_video(current_user.id, file_data, file.filename)

    return {
        "success": True,
        "video_url": result["url"]
    }


@router.post("/upload-post-image-url", status_code=status.HTTP_200_OK)
async def upload_post_image_from_url(
    image_url: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Upload an image for a post from URL

    **Request:**
    ```json
    {
      "image_url": "https://example.com/image.jpg"
    }
    ```

    **Returns:**
    ```json
    {
      "success": true,
      "image_url": "https://s3.amazonaws.com/..."
    }
    ```
    """
    import httpx
    s3_service = S3Service()

    # Download image from URL
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        response.raise_for_status()
        file_data = response.content

    # Extract filename from URL
    filename = image_url.split("/")[-1] or "image.jpg"

    # Upload to S3
    result = await s3_service.upload_post_image(current_user.id, file_data, filename)

    return {
        "success": True,
        "image_url": result["url"]
    }


# ============================================================
# CHANNEL POSTS ENDPOINTS
# ============================================================

@router.get("/channel/{channel_id}", response_model=PostListResponse, status_code=status.HTTP_200_OK)
async def get_channel_posts(
    channel_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get all posts from a specific channel

    **Requirements:**
    - User must be subscribed to the channel
    """
    return await post_service.get_posts_feed(
        user_id=current_user.id,
        channel_id=channel_id,
        page=page,
        page_size=page_size
    )


@router.get("/user/{user_id}", response_model=PostListResponse, status_code=status.HTTP_200_OK)
async def get_user_posts(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get all posts from a specific user

    **Note:** Only returns posts from channels the current user is subscribed to
    """
    return await post_service.get_posts_feed(
        user_id=current_user.id,
        author_id=user_id,
        page=page,
        page_size=page_size
    )


@router.get("/event/{event_id}", response_model=PostListResponse, status_code=status.HTTP_200_OK)
async def get_event_posts(
    event_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get all posts related to a specific event

    **Note:** Only returns posts from channels the current user is subscribed to
    """
    return await post_service.get_posts_feed(
        user_id=current_user.id,
        event_id=event_id,
        page=page,
        page_size=page_size
    )


# ============================================================
# POST MODERATION ENDPOINTS
# ============================================================

@router.post("/post-publish/{postId}", status_code=status.HTTP_200_OK)
async def publish_post(
    postId: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Publish a post (make it visible)

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await post_service.publish_post(postId)


@router.post("/post-unpublish/{postId}", status_code=status.HTTP_200_OK)
async def unpublish_post(
    postId: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Unpublish a post (hide it)

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await post_service.unpublish_post(postId)


@router.post("/post-mark-reviewed/{postId}", status_code=status.HTTP_200_OK)
async def mark_post_reviewed(
    postId: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Mark a post as reviewed by moderator

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await post_service.mark_post_reviewed(postId)


@router.post("/suspect_post/{postId}", status_code=status.HTTP_200_OK)
async def suspect_post(
    postId: int,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Mark a post as suspect/reported

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    return await post_service.mark_post_suspect(postId)


@router.get("/get-post-prays-extended/{id_code}", status_code=status.HTTP_200_OK)
async def get_post_prays_extended(
    id_code: str,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get extended pray information including user details

    **Response:**
    ```json
    {
      "prays": [
        {
          "user_id": 1,
          "username": "john_doe",
          "profile_image_url": "https://...",
          "created_at": "hace 2h"
        }
      ]
    }
    ```
    """
    return await post_service.get_post_prays_extended(id_code)
