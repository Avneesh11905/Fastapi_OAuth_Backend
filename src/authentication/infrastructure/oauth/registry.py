"""
Module: Registry
"""
from typing import Callable, Awaitable, Any
from authlib.integrations.starlette_client import OAuth  # type: ignore
from src.shared.infrastructure.logger import AsyncSQLLogger
from src.authentication.core.domain.user import OAuthUserInfo

logger = AsyncSQLLogger("OAuthRegistry")

class OAuthRegistry:
    def __init__(self):
        self.oauth = OAuth()
        self.providers: dict[str, Any] = {}
        self.parsers: dict[str, Callable[[Any, dict], Awaitable[OAuthUserInfo]]] = {}

    def register_provider(self, name: str, **kwargs):
        """
        Decorator to register a new OAuth provider and its user parser.
        
        @oauth_registry.register_provider("google", client_id=..., client_secret=...)
        async def parse_google(provider, token) -> OAuthUserInfo:
            ...
        """
        def decorator(parser_func: Callable[[Any, dict], Awaitable[OAuthUserInfo]]):
            self.oauth.register(name=name, **kwargs)
            
            # Authlib binds the client to the oauth object using the provider name
            provider_client = getattr(self.oauth, name)
            
            self.providers[name] = provider_client
            self.parsers[name] = parser_func
            return parser_func
            
        return decorator

# Global registry instance
oauth_registry = OAuthRegistry()
