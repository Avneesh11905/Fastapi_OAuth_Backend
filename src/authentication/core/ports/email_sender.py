"""
Port: Email Sender (Authentication Domain)

Defines the interface for sending auth-specific transactional emails.
Each domain defines its own email sender port with domain-specific methods.
"""
from typing import Protocol


class EmailSenderPort(Protocol):
    """Interface for sending authentication transactional emails."""

    async def send_welcome_email(self, to_email: str, name: str | None) -> None:
        """Send a welcome email to a newly registered user."""
        ...

    async def send_password_reset_email(self, to_email: str, reset_url: str) -> None:
        """Send a password reset email."""
        ...

    async def send_verification_email(self, to_email: str, otp: str) -> None:
        """Send an email address verification email containing a 6-digit OTP."""
        ...

    async def send_account_restored_email(self, to_email: str, name: str | None) -> None:
        """Send an email notifying the user that their account has been restored."""
        ...
