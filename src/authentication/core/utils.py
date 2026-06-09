import hmac
import hashlib
from src.shared.config import app_settings

def hash_otp(otp: str) -> str:
    """Hashes an OTP securely using HMAC-SHA256 with the application's session secret."""
    secret = app_settings.SESSION_SECRET.encode()
    return hmac.new(secret, otp.encode(), hashlib.sha256).hexdigest()

def verify_otp_hash(provided_otp: str, stored_hash: str) -> bool:
    """Verifies a provided OTP against the stored HMAC hash securely."""
    expected_hash = hash_otp(provided_otp)
    return hmac.compare_digest(expected_hash, stored_hash)
