"""
Module: Session
Contains pure domain entities related to tracking user sessions and devices.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ClientMetadata(BaseModel):
    """Metadata about the client making the request (e.g., extracted from HTTP headers)."""
    ip_address: str | None = None
    user_agent: str | None = None

class ActiveSession(BaseModel):
    """Represents an active, unexpired login session for a user."""
    family_id: UUID
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_active: datetime
    is_current: bool
    auth_provider: str
