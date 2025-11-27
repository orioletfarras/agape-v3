"""Tutored accounts endpoints - for parents managing children accounts"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.dependencies import get_current_user

router = APIRouter(tags=["Tutored Accounts"], prefix="")


@router.get("/tutored-accounts", status_code=status.HTTP_200_OK)
async def get_tutored_accounts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Get accounts tutored by current user (children accounts)

    **Response:**
    ```json
    {
      "children": [
        {
          "id": 123,
          "nombre": "Juan",
          "apellidos": "García",
          "dni": "12345678A",
          "correo_electronico": "juan@example.com",
          "fecha_nacimiento": "2010-05-15",
          "genero": "M",
          "parroquia_principal": "San Pedro"
        }
      ]
    }
    ```
    """
    # In a real implementation, you would have a TutoredAccount model
    # linking tutors (parents) to tutored users (children)
    # For now, returning empty array
    return {
        "children": []
    }
