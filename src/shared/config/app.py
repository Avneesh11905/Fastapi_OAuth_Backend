"""
Loads generic application configuration from the environment using Pydantic Settings.
Defines global settings like debug mode, host, port, and CORS origins.
"""
from .base import _BaseSettings
from typing import Optional
from pydantic_settings import SettingsConfigDict

from pydantic import field_validator

class URLSettings(_BaseSettings):
    FRONTEND_URL: str = "http://localhost:3000"

    @field_validator("FRONTEND_URL")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


def split_origins(v: str | list[str]) -> list[str]:
    if isinstance(v, str):
        return [i.strip() for i in v.split(",") if i.strip()]
    return v

class AppSettings(_BaseSettings):
    ENV: str = "development"
    PROJECT_NAME: str = "FastAPI OAuth"
    SESSION_SECRET: str
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str
    CORS_ORIGINS: Optional[str] = None
    COOKIE_DOMAIN: str | None = None
    COOKIE_PATH: str = "/"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return []
        # Strip whitespace and trailing slashes to prevent subtle CORS failures
        return [i.strip().rstrip("/") for i in self.CORS_ORIGINS.split(",") if i.strip()]

class CookieSettings:
    """Non-env cookie settings derived from app_settings."""
    def __init__(self, env: str, domain: str | None = None, path: str = "/"):
        self.SECURE = (env != "development")
        self.HTTP_ONLY = True
        self.SAMESITE = "none" if env != "development" else "lax"
        self.DOMAIN = domain
        self.PATH = path

class LogSettings(_BaseSettings):
    RETENTION_DAYS: int = 28

    model_config = SettingsConfigDict(**(_BaseSettings.model_config | {"env_prefix": "LOG_"}))
