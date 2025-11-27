from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserEntity:
    """Domain entity for User - represents business logic"""

    id: Optional[int]
    email: str
    full_name: str
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    def activate(self) -> None:
        """Activate user account"""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False

    def update_profile(self, full_name: Optional[str] = None) -> None:
        """Update user profile"""
        if full_name:
            self.full_name = full_name
