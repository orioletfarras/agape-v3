from fastapi import APIRouter
from app.api.v1 import auth, profile, organizations

router = APIRouter()

# Include all v1 routers
router.include_router(auth.router)
router.include_router(profile.router)
router.include_router(organizations.router)

__all__ = ["router"]
