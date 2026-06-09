"""
Shared utilities for the Refresh Token adapters.
Responsible for cryptographically hashing the opaque refresh tokens (using SHA-256) before they are stored in the database.
This ensures that a database leak does not expose valid refresh tokens.
"""
from hashlib import sha256

CACHE_TTL = 300  # 5 minutes
CACHE_KEY_PREFIX = "session"

def hash_token(raw_token: str) -> str:
    """One-way hash a raw token for storage and lookup."""
    return sha256(raw_token.encode()).hexdigest()

def cache_key(token_hash: str) -> str:
    """Derive a cache key from a token hash."""
    return f"{CACHE_KEY_PREFIX}:{token_hash}"


