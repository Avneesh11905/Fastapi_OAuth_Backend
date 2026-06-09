"""
Loads OAuth provider credentials (Client IDs and Secrets).
Provides configuration for Google, GitHub, and any future third-party identity providers.
"""
from .base import _BaseSettings
from pydantic_settings import SettingsConfigDict

class OAuthSettings(_BaseSettings):
    """
    Dynamic OAuth Settings loader.
    Allows fetching any OAuth credentials from the environment automatically.
    """
    model_config = SettingsConfigDict(
        **(_BaseSettings.model_config | {"extra": "allow"})
    )

    def get_credentials(self, provider: str) -> tuple[str, str]:
        """
        Retrieves the CLIENT_ID and CLIENT_SECRET for a given provider from the environment.
        Checks for exact matches, lowercase, and uppercase variants (e.g. DISCORD_CLIENT_ID).
        """
        keys_to_check = [
            f"{provider.upper()}_CLIENT_ID", f"{provider.lower()}_client_id",
            f"{provider.upper()}_CLIENT_SECRET", f"{provider.lower()}_client_secret"
        ]
        
        # We can dynamically access extra fields added via .env because of `extra="allow"`
        client_id = getattr(self, keys_to_check[0], getattr(self, keys_to_check[1], None))
        client_secret = getattr(self, keys_to_check[2], getattr(self, keys_to_check[3], None))
        
        if not client_id or not client_secret:
            raise ValueError(
                f"Missing OAuth credentials for provider: '{provider}'. "
                f"Please ensure {keys_to_check[0]} and {keys_to_check[2]} are set in your .env file."
            )
            
        return client_id, client_secret
