"""Organizations and parishes endpoints"""
from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.infrastructure.database.models import Organization, Parish
from pydantic import BaseModel

router = APIRouter(tags=["Organizations"])


# Schemas
class OrganizationResponse(BaseModel):
    id: int
    name: str
    image_url: str | None

    class Config:
        from_attributes = True


class ParishResponse(BaseModel):
    id: int
    name: str
    address: str | None

    class Config:
        from_attributes = True


@router.get("/organizations", response_model=List[OrganizationResponse], status_code=status.HTTP_200_OK)
async def list_organizations(
    session: AsyncSession = Depends(get_db),
):
    """
    List all organizations

    Returns all available organizations
    """
    result = await session.execute(select(Organization))
    organizations = result.scalars().all()

    return organizations


@router.get("/search-parishes", response_model=dict, status_code=status.HTTP_200_OK)
async def search_parishes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(1000, ge=1, le=1000),
    session: AsyncSession = Depends(get_db),
):
    """
    Search parishes by name

    Returns parishes matching the search query
    """
    # Search by name
    result = await session.execute(
        select(Parish)
        .where(Parish.name.ilike(f"%{q}%"))
        .limit(limit)
    )
    parishes = result.scalars().all()

    return {
        "parishes": [
            {
                "id": p.id,
                "name": p.name,
                "address": p.address,
            }
            for p in parishes
        ]
    }
