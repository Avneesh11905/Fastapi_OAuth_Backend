"""
Module: Google
"""
from src.authentication.core.domain.user import OAuthUserInfo
from src.authentication.infrastructure.oauth.registry import oauth_registry
from src.shared.config import oauth_settings

client_id, client_secret = oauth_settings.get_credentials("google")

@oauth_registry.register_provider(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=client_id,
    client_secret=client_secret,
    client_kwargs={"scope": "openid email profile"},
    authorize_params={"prompt": "consent"},
)
async def parse_google_user(provider, token) -> OAuthUserInfo:
    google_info = token.get("userinfo")
    if not google_info:
        google_info = await provider.userinfo(token=token)
    google_info = dict(google_info)
    if not google_info.get("email_verified"):
        raise ValueError("Google email not verified")
    
    return OAuthUserInfo(
        sub=google_info["sub"],
        email=google_info["email"],
        name=google_info.get("name"),
        picture=google_info.get("picture"),
        provider="google",
    )
