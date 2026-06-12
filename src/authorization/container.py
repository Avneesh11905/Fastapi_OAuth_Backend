"""
Dependency Injection Container for Authorization Boilerplate
"""
from src.authorization.adapters.custom_authorization import CustomAuthorizationAdapter

# This adapter is automatically picked up by `src/authentication/container.py`
# If you export it here as `custom_claims_provider`, the Authentication domain
# will start injecting JWTs with the claims returned by `get_custom_claims()`.
custom_claims_provider = CustomAuthorizationAdapter()
