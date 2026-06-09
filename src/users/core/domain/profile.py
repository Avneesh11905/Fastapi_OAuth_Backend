"""
Defines the pure domain entity for a User Profile.
This dataclass contains no infrastructure dependencies (like SQLAlchemy or Pydantic),
ensuring the core business logic remains framework-agnostic.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class UserProfile:
    id: str
    email: str
    name: str | None
    picture: str | None
    receive_updates: bool
    login_methods: list[str]
