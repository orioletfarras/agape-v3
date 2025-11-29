"""Translation endpoints for i18n"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
import httpx
from typing import Optional

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User, Translation
from app.api.dependencies import get_current_user

router = APIRouter(tags=["Translations"], prefix="")


class GetTranslationRequest(BaseModel):
    key: str
    language: str


class SaveTranslationRequest(BaseModel):
    key: str
    translation: str
    language: str


@router.post("/get-translation", status_code=status.HTTP_200_OK)
async def get_translation(
    request: GetTranslationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get translation for text from database or external API

    **Request:**
    ```json
    {
      "key": "Edit post",
      "language": "es"
    }
    ```

    **Response:**
    ```json
    {
      "translation": "Editar publicación"
    }
    ```
    """
    # Try to get from database first
    stmt = select(Translation).where(
        and_(
            Translation.key == request.key,
            Translation.language == request.language
        )
    )
    result = await session.execute(stmt)
    db_translation = result.scalar_one_or_none()
    
    if db_translation:
        return {"translation": db_translation.translation}
    
    # If not in DB, try MyMemory API
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.mymemory.translated.net/get?q={request.key}&langpair=ca|{request.language}"
            response = await client.get(url, timeout=10.0)
            data = response.json()
            
            translation_text = data.get("responseData", {}).get("translatedText")
            
            # Try to find best match
            if data.get("matches"):
                exact_match = next((m for m in data["matches"] if m.get("segment") == request.key), None)
                if exact_match and exact_match.get("translation"):
                    translation_text = exact_match["translation"]
                elif data["matches"]:
                    best_match = max(data["matches"], key=lambda m: m.get("match", 0))
                    if best_match.get("translation"):
                        translation_text = best_match["translation"]
            
            if translation_text:
                # Save to database for future use
                new_translation = Translation(
                    key=request.key,
                    translation=translation_text,
                    language=request.language
                )
                session.add(new_translation)
                await session.commit()
                
                return {"translation": translation_text}
    except Exception as e:
        # If external API fails, return original key
        pass
    
    # Return original key if no translation found
    return {"translation": request.key}


@router.post("/save-translation", status_code=status.HTTP_200_OK)
async def save_translation(
    request: SaveTranslationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Save a translation for caching/reuse

    **Request:**
    ```json
    {
      "key": "Edit post",
      "translation": "Editar publicación",
      "language": "es"
    }
    ```

    **Response:**
    ```json
    {
      "success": true
    }
    ```
    """
    # Check if translation already exists
    stmt = select(Translation).where(
        and_(
            Translation.key == request.key,
            Translation.language == request.language
        )
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing translation
        existing.translation = request.translation
    else:
        # Create new translation
        new_translation = Translation(
            key=request.key,
            translation=request.translation,
            language=request.language
        )
        session.add(new_translation)
    
    await session.commit()
    
    return {"success": True}
