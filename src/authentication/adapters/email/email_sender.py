"""
Integrates with the Resend API to send transactional emails (OTPs, Welcome, Password Resets).
"""
import resend
from pathlib import Path
from src.shared.core.ports.logger import LoggerPort
from src.shared.core.ports.task_runner import TaskRunnerPort
from .base_email_sender import BaseEmailAdapter
import asyncio

class ResendAdapter(BaseEmailAdapter):
    """Implements BaseEmailAdapter using the Resend API."""

    def __init__(self, api_key: str, from_email: str, templates_dir: Path, logger: LoggerPort, proj_name: str, template_name: str, frontend_url: str, task_runner: TaskRunnerPort):
        super().__init__(from_email, templates_dir, logger, proj_name, template_name, frontend_url, task_runner)
        self._api_key = api_key
        resend.api_key = api_key

    async def _dispatch_email(self, to_email: str, subject: str, html_content: str) -> None:
        params = {
            "from": self._from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: resend.Emails.send(params)) # type: ignore
