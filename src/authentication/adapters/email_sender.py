"""
Adapter: Auth Email Service

Implements EmailSenderPort for the authentication domain.
Handles all auth-specific email composition (Jinja rendering, background task queuing)
and delegates the actual dispatch to the injected SharedEmailClientPort.

To swap the email provider (e.g. Resend -> SendGrid), replace the SharedEmailClientPort
implementation in the container — this file never changes.
"""
from pathlib import Path
import datetime
from jinja2 import Environment, FileSystemLoader
import asyncio
from src.authentication.core.ports.email_sender import EmailSenderPort  # noqa: F401
from src.shared.core.ports.email_client import SharedEmailClientPort
from src.shared.core.ports.logger import LoggerPort
from src.shared.core.ports.task_runner import TaskRunnerPort


class AuthEmailService:
    """
    Implements EmailSenderPort for authentication emails.
    Composes domain-specific emails (Welcome, OTP, Password Reset) using Jinja2 templates
    and dispatches them via the injected SharedEmailClientPort.
    """

    def __init__(
        self,
        email_client: SharedEmailClientPort,
        from_email: str,
        templates_dir: Path,
        logger: LoggerPort,
        proj_name: str,
        template_name: str,
        frontend_url: str,
        task_runner: TaskRunnerPort,
    ) -> None:
        self._client = email_client
        self._from_email = f"{proj_name} <{from_email}>"
        self._logger = logger
        self._proj_name = proj_name
        self._template_name = template_name
        self._frontend_url = frontend_url
        self._task_runner = task_runner

        self._jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        self._jinja_env.globals["now"] = datetime.datetime.now

    async def _render_and_send(self, to_email: str, subject: str, template_name: str, context: dict) -> None:
        try:
            template = self._jinja_env.get_template(template_name)
            html_content = template.render(**context)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._client.send_email, to_email, subject, html_content)
            await self._logger.info(f"Email '{subject}' sent to {to_email}")
        except Exception as e:
            await self._logger.error(f"Failed to send email '{subject}' to {to_email}: {e}")

    async def send_welcome_email(self, to_email: str, name: str | None) -> None:
        display_name = name or "there"
        context = {
            "name": display_name,
            "proj_name": self._proj_name,
            "login_url": f"{self._frontend_url}/",
            "theme": self._template_name,
        }
        self._task_runner.add_task(
            self._render_and_send,
            to_email=to_email,
            subject=f"Welcome to {self._proj_name}!",
            template_name="onboarding/welcome.html",
            context=context,
        )

    async def send_password_reset_email(self, to_email: str, reset_url: str) -> None:
        context = {
            "reset_url": reset_url,
            "proj_name": self._proj_name,
            "theme": self._template_name,
        }
        self._task_runner.add_task(
            self._render_and_send,
            to_email=to_email,
            subject=f"Password Reset - {self._proj_name}",
            template_name="security/password_reset.html",
            context=context,
        )

    async def send_verification_email(self, to_email: str, otp: str) -> None:
        context = {
            "otp": otp,
            "proj_name": self._proj_name,
            "theme": self._template_name,
        }
        self._task_runner.add_task(
            self._render_and_send,
            to_email=to_email,
            subject=f"Verify your Email - {self._proj_name}",
            template_name="security/otp_verification.html",
            context=context,
        )
