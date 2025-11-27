"""Reactions domain schemas"""
from pydantic import BaseModel


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class ToggleReactionRequest(BaseModel):
    """Request to toggle a reaction"""
    action: str  # "like" or "unlike"


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class ReactionResponse(BaseModel):
    """Reaction response"""
    success: bool
    is_reacted: bool
    message: str
    reaction_count: int = 0
