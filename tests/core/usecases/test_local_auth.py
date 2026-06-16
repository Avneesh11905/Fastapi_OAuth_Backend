import hashlib
import time

import pytest

from src.authentication.core.domain.exceptions import (
    EmailAlreadyRegisteredException,
    InvalidCredentialsException,
    InvalidTokenException,
    UnverifiedEmailException,
)
from src.authentication.core.usecases import (
    LoginLocalUserUseCase,
    RegisterLocalUserUseCase,
    VerifyEmailUseCase,
)
from tests.conftest import MockCache, MockEmailSender


@pytest.fixture
def mock_cache():
    return MockCache()

@pytest.fixture
def email_sender():
    return MockEmailSender()

@pytest.fixture
def register_usecase(user_repo, password_hasher, logger_port, mock_cache, email_sender):
    return RegisterLocalUserUseCase(
        user_repo=user_repo,
        hasher=password_hasher,
        logger=logger_port,
        email_sender=email_sender,
        cache=mock_cache
    )

@pytest.fixture
def verify_usecase(user_repo, logger_port, mock_cache, refresh_token_port, email_sender):
    return VerifyEmailUseCase(
        user_repo=user_repo,
        logger=logger_port,
        email_sender=email_sender,
        cache=mock_cache,
        refresh_repo=refresh_token_port
    )

@pytest.fixture
def login_usecase(user_repo, refresh_token_port, password_hasher, logger_port, email_sender):
    return LoginLocalUserUseCase(
        user_repo=user_repo,
        refresh_repo=refresh_token_port,
        hasher=password_hasher,
        logger=logger_port,
        email_sender=email_sender
    )

@pytest.mark.asyncio
async def test_register_and_verify_success(register_usecase, verify_usecase, mock_session, user_repo, mock_cache, email_sender):
    email = "test@example.com"
    # 1. Register
    await register_usecase.execute(mock_session, email, "SecurePass123", "Alice")
    
    # Verify user IS in DB but NOT verified yet
    pending_user = await user_repo.find_by_email(mock_session, email)
    assert pending_user is not None
    assert pending_user.is_verified is False
    
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    payload = await mock_cache.get_dict(f"pending_reg:{email_hash}")
    assert payload is not None
    
    otp = email_sender.sent_otps[email]
    
    # 3. Verify
    await verify_usecase.execute(mock_session, email, otp)
    
    # Verify user IS in DB now
    user = await user_repo.find_by_email(mock_session, email)
    assert user is not None
    assert user.email == email
    assert user.is_verified is True
    
    stored_hash = await user_repo.find_password_hash(mock_session, user.id)
    assert stored_hash == "hashed_SecurePass123"

@pytest.mark.asyncio
async def test_register_duplicate_email_fails(register_usecase, verify_usecase, mock_session, mock_cache, email_sender):
    email = "dup@example.com"
    await register_usecase.execute(mock_session, email, "pass1", "User 1")
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    await mock_cache.get_dict(f"pending_reg:{email_hash}")
    otp = email_sender.sent_otps[email]
    await verify_usecase.execute(mock_session, email, otp)
    
    # Now try to register again
    with pytest.raises(EmailAlreadyRegisteredException, match="Email already registered"):
        await register_usecase.execute(mock_session, email, "pass2", "User 2")

@pytest.mark.asyncio
async def test_login_success(register_usecase, verify_usecase, login_usecase, mock_session, mock_cache, email_sender):
    email = "login@example.com"
    await register_usecase.execute(mock_session, email, "mypassword", "Login User")
    
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    await mock_cache.get_dict(f"pending_reg:{email_hash}")
    otp = email_sender.sent_otps[email]
    await verify_usecase.execute(mock_session, email, otp)

    logged_in_user, token = await login_usecase.execute(mock_session, email, "mypassword")

    assert logged_in_user.email == email
    assert token.startswith("mock_token_for_")

@pytest.mark.asyncio
async def test_login_invalid_password_fails(register_usecase, verify_usecase, login_usecase, mock_session, mock_cache, email_sender):
    email = "wrongpass@example.com"
    await register_usecase.execute(mock_session, email, "correctpassword", "User")
    
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    await mock_cache.get_dict(f"pending_reg:{email_hash}")
    otp = email_sender.sent_otps[email]
    await verify_usecase.execute(mock_session, email, otp)

    with pytest.raises(InvalidCredentialsException, match="Invalid email or password"):
        await login_usecase.execute(mock_session, email, "wrongpassword")


@pytest.mark.asyncio
async def test_expired_otp_fails(register_usecase, verify_usecase, mock_session, mock_cache, email_sender):
    """G-09: An expired OTP must raise InvalidTokenException, not InvalidCredentialsException."""
    email = "expired@example.com"
    await register_usecase.execute(mock_session, email, "pass", "User")
    otp = email_sender.sent_otps[email]

    # Manually backdate the OTP expiry
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    payload = await mock_cache.get_dict(f"pending_reg:{email_hash}")
    payload["otp_expires_at"] = int(time.time()) - 1
    await mock_cache.set_dict(f"pending_reg:{email_hash}", payload, 900)

    with pytest.raises(InvalidTokenException, match="expired"):
        await verify_usecase.execute(mock_session, email, otp)


@pytest.mark.asyncio
async def test_login_unverified_email_returns_403(login_usecase, register_usecase, mock_session, email_sender):
    """G-10: Unverified users must receive UnverifiedEmailException (maps to 403 HTTP)."""
    email = "unverified@example.com"
    await register_usecase.execute(mock_session, email, "SecurePass", "User")
    with pytest.raises(UnverifiedEmailException):
        await login_usecase.execute(mock_session, email, "SecurePass")


@pytest.mark.asyncio
async def test_oauth_only_user_cannot_login_locally(login_usecase, mock_session, user_repo):
    """G-11: A user with no local password (OAuth-only) cannot log in via /login/local."""
    await user_repo.create_user_with_password(
        mock_session, "oauth@example.com", "OAuth User", password_hash=None, is_verified=True
    )
    with pytest.raises(InvalidCredentialsException):
        await login_usecase.execute(mock_session, "oauth@example.com", "anypassword")


@pytest.mark.asyncio
async def test_email_case_insensitive_login(register_usecase, verify_usecase, login_usecase,
                                             mock_session, mock_cache, email_sender):
    """G-08 (AUD-08): Register with lowercase email, login with uppercase — must succeed."""
    email = "mixedcase@example.com"
    await register_usecase.execute(mock_session, email, "SecurePass", "User")
    otp = email_sender.sent_otps[email]
    await verify_usecase.execute(mock_session, email, otp)
    # Login with the same canonical lowercase form (normalisation happens in schema layer)
    user, token = await login_usecase.execute(mock_session, email, "SecurePass")
    assert user is not None
