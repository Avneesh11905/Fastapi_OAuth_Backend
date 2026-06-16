import importlib
import pkgutil

from src.shared.adapters.logger import AsyncSQLLogger

from . import providers
from .registry import oauth_registry

logger = AsyncSQLLogger("OAuthAutoDiscovery")

def _discover_providers():
    """
    Dynamically loads all modules inside the `providers` package.
    This triggers their @oauth_registry.register_provider decorators.
    """
    package = providers
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        try:
            importlib.import_module(f"{package.__name__}.{module_name}")
        except Exception as e:
            # We must use print here since this is synchronous module-level code
            # and AsyncSQLLogger is async. A proper startup task could await the logger.
            print(f"[OAuthAutoDiscovery] Failed to load provider '{module_name}': {e}")

# Run discovery at import time
_discover_providers()

# Export what the rest of the application needs
PROVIDERS = oauth_registry.providers
PARSERS = oauth_registry.parsers
oauth = oauth_registry.oauth

__all__ = ["PROVIDERS", "PARSERS", "oauth"]
