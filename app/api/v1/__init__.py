from fastapi import APIRouter
from app.api.v1 import auth, profile, organizations, posts, channels, events

router = APIRouter()

# Include all v1 routers
router.include_router(auth.router)
router.include_router(profile.router)
router.include_router(organizations.router)
router.include_router(posts.router)
router.include_router(channels.router)
router.include_router(events.router)

__all__ = ["router"]
