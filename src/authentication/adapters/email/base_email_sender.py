"""
Base Email Adapter
Provides the common logic for rendering Jinja templates and queuing background email tasks.
Specific providers (Resend, SendGrid, Mailgun) just need to inherit this and implement `_dispatch_email`.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import datetime
from src.authentication.core.ports.email.email_sender import EmailSenderPort
from src.shared.core.ports.logger import LoggerPort
from src.shared.core.ports.task_runner import TaskRunnerPort

class BaseEmailAdapter(EmailSenderPort):
    """Abstract base class for email sending adapters."""

    def __init__(self, from_email: str, templates_dir: Path, logger: LoggerPort, proj_name: str, template_name: str, frontend_url: str, task_runner: TaskRunnerPort):
        self._from_email = f"{proj_name} <{from_email}>"
        self._logger = logger
        self._proj_name = proj_name
        self._template_name = template_name
        self._frontend_url = frontend_url
        self._task_runner = task_runner
        
        self._jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        self._jinja_env.globals["now"] = datetime.datetime.now

    async def _dispatch_email(self, to_email: str, subject: str, html_content: str) -> None:
        """Override this method in the concrete provider (e.g., ResendAdapter)."""
        raise NotImplementedError("Must be implemented by concrete email adapter")

    async def _render_and_send(self, to_email: str, subject: str, template_name: str, context: dict) -> None:
        try:
            template = self._jinja_env.get_template(template_name)
            html_content = template.render(**context)
            await self._dispatch_email(to_email, subject, html_content)
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
