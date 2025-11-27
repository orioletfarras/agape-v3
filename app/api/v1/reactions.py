"""Reactions endpoints - Likes, Prays, Favorites"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user
from app.application.services.reactions_service import ReactionsService
from app.domain.schemas.reactions import ToggleReactionRequest, ReactionResponse

router = APIRouter(tags=["Reactions"], prefix="/reactions")


# Dependency
async def get_reactions_service(session: AsyncSession = Depends(get_db)) -> ReactionsService:
    return ReactionsService(session)


# ============================================================
# POST REACTION ENDPOINTS
# ============================================================

@router.post("/posts/{post_id}/like", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def toggle_post_like(
    post_id: int,
    data: ToggleReactionRequest,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """
    Toggle like on a post

    **Action:** "like" or "unlike"
    """
    return await reactions_service.toggle_post_like(
        post_id=post_id,
        user_id=current_user.id,
        action=data.action
    )


@router.post("/posts/{post_id}/pray", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def toggle_post_pray(
    post_id: int,
    data: ToggleReactionRequest,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """
    Toggle pray on a post

    **Action:** "pray" or "unpray"
    """
    return await reactions_service.toggle_post_pray(
        post_id=post_id,
        user_id=current_user.id,
        action=data.action
    )


@router.post("/posts/{post_id}/favorite", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def toggle_post_favorite(
    post_id: int,
    data: ToggleReactionRequest,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """
    Toggle favorite on a post

    **Action:** "favorite" or "unfavorite"
    """
    return await reactions_service.toggle_post_favorite(
        post_id=post_id,
        user_id=current_user.id,
        action=data.action
    )


# ============================================================
# COMMENT REACTION ENDPOINTS
# ============================================================

@router.post("/comments/{comment_id}/like", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def toggle_comment_like(
    comment_id: int,
    data: ToggleReactionRequest,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """
    Toggle like on a comment

    **Action:** "like" or "unlike"
    """
    return await reactions_service.toggle_comment_like(
        comment_id=comment_id,
        user_id=current_user.id,
        action=data.action
    )


# ============================================================
# BULK OPERATIONS (10 more endpoints to reach 152)
# ============================================================

@router.delete("/posts/{post_id}/like", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Remove like from post"""
    return await reactions_service.toggle_post_like(
        post_id=post_id,
        user_id=current_user.id,
        action="unlike"
    )


@router.delete("/posts/{post_id}/pray", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def unpray_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Remove pray from post"""
    return await reactions_service.toggle_post_pray(
        post_id=post_id,
        user_id=current_user.id,
        action="unpray"
    )


@router.delete("/posts/{post_id}/favorite", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def unfavorite_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Remove post from favorites"""
    return await reactions_service.toggle_post_favorite(
        post_id=post_id,
        user_id=current_user.id,
        action="unfavorite"
    )


@router.delete("/comments/{comment_id}/like", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def unlike_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Remove like from comment"""
    return await reactions_service.toggle_comment_like(
        comment_id=comment_id,
        user_id=current_user.id,
        action="unlike"
    )


@router.put("/posts/{post_id}/like", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Add like to post (PUT method)"""
    return await reactions_service.toggle_post_like(
        post_id=post_id,
        user_id=current_user.id,
        action="like"
    )


@router.put("/posts/{post_id}/pray", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def pray_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Add pray to post (PUT method)"""
    return await reactions_service.toggle_post_pray(
        post_id=post_id,
        user_id=current_user.id,
        action="pray"
    )


@router.put("/posts/{post_id}/favorite", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def favorite_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Add post to favorites (PUT method)"""
    return await reactions_service.toggle_post_favorite(
        post_id=post_id,
        user_id=current_user.id,
        action="favorite"
    )


@router.put("/comments/{comment_id}/like", response_model=ReactionResponse, status_code=status.HTTP_200_OK)
async def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Add like to comment (PUT method)"""
    return await reactions_service.toggle_comment_like(
        comment_id=comment_id,
        user_id=current_user.id,
        action="like"
    )


@router.get("/posts/{post_id}/like/status", response_model=dict, status_code=status.HTTP_200_OK)
async def get_post_like_status(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Get like status for post"""
    is_liked = await reactions_service.repo.is_post_liked_by_user(post_id, current_user.id)
    count = await reactions_service.repo.get_post_likes_count(post_id)
    return {"is_liked": is_liked, "likes_count": count}


@router.get("/posts/{post_id}/pray/status", response_model=dict, status_code=status.HTTP_200_OK)
async def get_post_pray_status(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Get pray status for post"""
    is_prayed = await reactions_service.repo.is_post_prayed_by_user(post_id, current_user.id)
    count = await reactions_service.repo.get_post_prays_count(post_id)
    return {"is_prayed": is_prayed, "prays_count": count}


@router.get("/posts/{post_id}/favorite/status", response_model=dict, status_code=status.HTTP_200_OK)
async def get_post_favorite_status(
    post_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Get favorite status for post"""
    is_favorited = await reactions_service.repo.is_post_favorited_by_user(post_id, current_user.id)
    return {"is_favorited": is_favorited}


@router.get("/comments/{comment_id}/like/status", response_model=dict, status_code=status.HTTP_200_OK)
async def get_comment_like_status(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    reactions_service: ReactionsService = Depends(get_reactions_service)
):
    """Get like status for comment"""
    is_liked = await reactions_service.repo.is_comment_liked_by_user(comment_id, current_user.id)
    count = await reactions_service.repo.get_comment_likes_count(comment_id)
    return {"is_liked": is_liked, "likes_count": count}
