"""
Port: Email

This module defines the interface (Port) for email.
Core business logic relies on these interfaces rather than concrete implementations.
"""
from typing import Protocol

class EmailSenderPort(Protocol):
    """Interface for sending transactional emails."""

    async def send_welcome_email(self, to_email: str, name: str | None) -> None:
        """Send a welcome email to a newly registered user."""
        ...

    async def send_password_reset_email(self, to_email: str, reset_url: str) -> None:
        """Send a password reset email."""
        ...

    async def send_verification_email(self, to_email: str, otp: str) -> None:
        """Send an email address verification email containing a 6-digit OTP."""
        ...
