"""
Provides the base class for all configuration models.
Ensures standard `.env` parsing behavior and strict typing across all config subsets.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class _BaseSettings(BaseSettings):
    """Shared configuration for all settings classes."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
