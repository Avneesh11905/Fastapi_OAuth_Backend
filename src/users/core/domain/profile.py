"""
Defines the pure domain entity for a User Profile.
This Pydantic model contains no infrastructure dependencies (like SQLAlchemy),
ensuring the core business logic remains framework-agnostic.
"""
from pydantic import BaseModel

class UserProfile(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None
    receive_updates: bool
    login_methods: list[str]
