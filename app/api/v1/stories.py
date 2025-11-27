"""Stories endpoints"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User, Story, Follow
from app.api.dependencies import get_current_user

router = APIRouter(tags=["Stories"], prefix="/stories")


@router.get("", status_code=status.HTTP_200_OK)
async def get_stories(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get stories from followed users (last 24 hours)

    **Response:**
    ```json
    {
      "stories": [
        {
          "id": 1,
          "user": {
            "id": 5,
            "username": "john_doe",
            "profile_image_url": "https://..."
          },
          "media_url": "https://...",
          "created_at": "2025-01-15T10:00:00"
        }
      ]
    }
    ```
    """
    # Get users that current user follows
    followed_users_result = await session.execute(
        select(Follow.followed_id).where(
            and_(
                Follow.follower_id == current_user.id,
                Follow.status == "accepted"
            )
        )
    )
    followed_user_ids = [row[0] for row in followed_users_result.all()]

    # Get stories from last 24 hours from followed users + own stories
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)

    result = await session.execute(
        select(Story, User)
        .join(User, Story.user_id == User.id)
        .where(
            and_(
                or_(
                    Story.user_id.in_(followed_user_ids),
                    Story.user_id == current_user.id
                ),
                Story.created_at >= twenty_four_hours_ago
            )
        )
        .order_by(Story.created_at.desc())
    )

    stories = []
    for story, user in result.all():
        stories.append({
            "id": story.id,
            "user": {
                "id": user.id,
                "username": user.username,
                "profile_image_url": user.profile_image_url
            },
            "media_url": story.media_url,
            "created_at": story.created_at
        })

    return {"stories": stories}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_story(
    media_url: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Create a new story

    **Request:**
    ```json
    {
      "media_url": "https://s3.amazonaws.com/..."
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "story_id": 123
    }
    ```
    """
    story = Story(
        user_id=current_user.id,
        media_url=media_url,
        created_at=datetime.utcnow()
    )
    session.add(story)
    await session.commit()
    await session.refresh(story)

    return {
        "success": True,
        "story_id": story.id
    }


@router.delete("/{storyId}", status_code=status.HTTP_200_OK)
async def delete_story(
    storyId: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Delete a story (only own stories)

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    result = await session.execute(
        select(Story).where(
            and_(
                Story.id == storyId,
                Story.user_id == current_user.id
            )
        )
    )
    story = result.scalar_one_or_none()

    if not story:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found or not authorized"
        )

    await session.delete(story)
    await session.commit()

    return {"success": True}
