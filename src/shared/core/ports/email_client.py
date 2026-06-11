"""
Port: Shared Email Client

Defines the generic interface for dispatching a pre-rendered email.
Infrastructure adapters (Resend, SendGrid, Mailgun, etc.) implement this port.
Domain-specific email services (e.g. AuthEmailService) depend on this port
so that swapping the email provider only requires changing one file in shared/adapters.
"""
from typing import Protocol


class SharedEmailClientPort(Protocol):
    """Generic interface for sending a single transactional email."""

    def send_email(self, to: str, subject: str, html: str) -> None:
        """Dispatch a pre-rendered HTML email to the given recipient."""
        ...
