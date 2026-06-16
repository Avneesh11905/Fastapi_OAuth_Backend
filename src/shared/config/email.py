"""
Loads email provider configuration (e.g., Resend API keys).
Specifies the default sender address and fallback template themes.
"""
from pydantic_settings import SettingsConfigDict

from .base import _BaseSettings


class EmailSettings(_BaseSettings):
    """Email settings."""
    API_KEY: str = "placeholder"
    FROM: str = "auth@localhost"
    TEMPLATE_NAME: str = "modern"

    model_config = SettingsConfigDict(**(_BaseSettings.model_config | {"env_prefix": "EMAIL_"}))
