"""
Module: User
"""
from pydantic import BaseModel

class UserIdentity(BaseModel):
    """Pure domain entity — now powered by Pydantic."""
    id: str
    email: str
    is_verified: bool
    name: str | None = None
    picture: str | None = None

class OAuthUserInfo(BaseModel):
    """Structured data returned by OAuth providers."""
    provider: str
    sub: str
    email: str
    name: str | None = None
    picture: str | None = None
