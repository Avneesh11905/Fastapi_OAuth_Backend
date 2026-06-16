"""
Loads authentication-specific configuration.
Defines secrets for JWT signing, expiration times, and algorithm preferences.
"""
from pydantic_settings import SettingsConfigDict

from .base import _BaseSettings


class TokenSettings(_BaseSettings):
    ACCESS_TOKEN_LIFETIME_MINUTES: int = 15
    REFRESH_TOKEN_LIFETIME_DAYS: int = 7

    model_config = SettingsConfigDict(**(_BaseSettings.model_config | {"env_prefix": "TOKEN_"}))

class VerificationSettings(_BaseSettings):
    OTP_EXPIRATION_SECONDS: int = 300
    OTP_RESEND_WINDOW_SECONDS: int = 900
    OTP_MAX_ATTEMPTS: int = 5
    PASSWORD_RESET_EXPIRY_SECONDS: int = 900

    model_config = SettingsConfigDict(**(_BaseSettings.model_config | {"env_prefix": "VERIFICATION_"}))

class RateLimitSettings(_BaseSettings):
    REFRESH_RATE_LIMIT: str = "30/minute"
    LOGIN_RATE_LIMIT: str = "5/minute"
    DEFAULT_RATE_LIMIT: str = "60/minute"

    model_config = SettingsConfigDict(**(_BaseSettings.model_config | {"env_prefix": "RATE_LIMIT_"}))
