from fastapi import APIRouter
from app.api.v1 import (
    auth, profile, organizations, posts, channels, events, comments, social,
    notifications, messaging, settings, admin, search, reactions, debug,
    prayer_life, donations, roles, tutored_accounts, stories, polls, tickets,
    translations, identity_verification, horariosdemisa
)

router = APIRouter()

# Include all v1 routers
router.include_router(auth.router)
router.include_router(profile.router)
router.include_router(organizations.router)
router.include_router(posts.router)
router.include_router(channels.router)
router.include_router(events.router)
router.include_router(comments.router)
router.include_router(social.router)
router.include_router(notifications.router)
router.include_router(messaging.router)
router.include_router(settings.router)
router.include_router(admin.router)
router.include_router(search.router)
router.include_router(reactions.router)
router.include_router(debug.router)
router.include_router(prayer_life.router)
router.include_router(donations.router)
router.include_router(roles.router)
router.include_router(tutored_accounts.router)
router.include_router(stories.router)
router.include_router(polls.router)
router.include_router(tickets.router)
router.include_router(translations.router)
router.include_router(identity_verification.router)
router.include_router(horariosdemisa.router)

__all__ = ["router"]
