"""Polls and voting endpoints"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User, Poll, PollOption, PollVote
from app.api.dependencies import get_current_user

router = APIRouter(tags=["Polls"], prefix="/polls")


@router.get("/{pollId}/results", status_code=status.HTTP_200_OK)
async def get_poll_results(
    pollId: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get poll results with vote counts and percentages

    **Response:**
    ```json
    {
      "poll_id": 1,
      "question": "¿Cuál es tu color favorito?",
      "options": [
        {
          "id": 1,
          "text": "Rojo",
          "votes": 25,
          "percentage": 50.0
        },
        {
          "id": 2,
          "text": "Azul",
          "votes": 25,
          "percentage": 50.0
        }
      ],
      "total_votes": 50,
      "user_voted": true,
      "user_vote_option_id": 1
    }
    ```
    """
    # Get poll
    poll_result = await session.execute(
        select(Poll).where(Poll.id == pollId)
    )
    poll = poll_result.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found"
        )

    # Get poll options with vote counts
    options_result = await session.execute(
        select(
            PollOption.id,
            PollOption.text,
            func.count(PollVote.id).label('votes')
        )
        .outerjoin(PollVote, PollOption.id == PollVote.option_id)
        .where(PollOption.poll_id == pollId)
        .group_by(PollOption.id, PollOption.text)
    )

    options = []
    total_votes = 0
    for option_id, text, votes in options_result.all():
        options.append({
            "id": option_id,
            "text": text,
            "votes": votes or 0
        })
        total_votes += (votes or 0)

    # Calculate percentages
    for option in options:
        if total_votes > 0:
            option["percentage"] = round((option["votes"] / total_votes) * 100, 1)
        else:
            option["percentage"] = 0.0

    # Check if user has voted
    user_vote_result = await session.execute(
        select(PollVote.option_id).where(
            PollVote.user_id == current_user.id
        ).join(PollOption).where(PollOption.poll_id == pollId)
    )
    user_vote_option = user_vote_result.scalar_one_or_none()

    return {
        "poll_id": poll.id,
        "question": poll.question,
        "options": options,
        "total_votes": total_votes,
        "user_voted": user_vote_option is not None,
        "user_vote_option_id": user_vote_option
    }


@router.post("/{pollId}/vote", status_code=status.HTTP_200_OK)
async def vote_on_poll(
    pollId: int,
    option_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Vote on a poll option

    **Request:**
    ```json
    {
      "option_id": 1
    }
    ```

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    # Check if poll exists
    poll_result = await session.execute(
        select(Poll).where(Poll.id == pollId)
    )
    poll = poll_result.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found"
        )

    # Check if option belongs to this poll
    option_result = await session.execute(
        select(PollOption).where(
            PollOption.id == option_id,
            PollOption.poll_id == pollId
        )
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll option not found"
        )

    # Check if user has already voted
    existing_vote_result = await session.execute(
        select(PollVote)
        .join(PollOption)
        .where(
            PollOption.poll_id == pollId,
            PollVote.user_id == current_user.id
        )
    )
    existing_vote = existing_vote_result.scalar_one_or_none()

    if existing_vote:
        # Update vote
        existing_vote.option_id = option_id
        existing_vote.voted_at = datetime.utcnow()
    else:
        # Create new vote
        vote = PollVote(
            option_id=option_id,
            user_id=current_user.id,
            voted_at=datetime.utcnow()
        )
        session.add(vote)

    await session.commit()

    return {"success": True}
