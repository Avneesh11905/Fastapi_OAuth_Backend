from .app import URLSettings, AppSettings, CookieSettings, LogSettings
from .auth import TokenSettings, RateLimitSettings
from .database import DatabaseSettings
from .email import EmailSettings
from .oauth import OAuthSettings

url_settings = URLSettings() # type: ignore
app_settings = AppSettings() # type: ignore
oauth_settings = OAuthSettings() # type: ignore
database_settings = DatabaseSettings() # type: ignore
email_settings = EmailSettings() # type: ignore
token_settings = TokenSettings() # type: ignore
rate_limit_settings = RateLimitSettings() # type: ignore
log_settings = LogSettings() # type: ignore
cookie_settings = CookieSettings(
    env=app_settings.ENV, 
    domain=app_settings.COOKIE_DOMAIN, 
    path=app_settings.COOKIE_PATH
)
