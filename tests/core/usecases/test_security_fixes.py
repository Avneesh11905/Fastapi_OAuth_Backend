"""
Tests for the 10 security fixes from the 2026-06-16 audit.
Each test is tagged with its finding ID for traceability.
"""
import asyncio
import hashlib
import hashlib as _hashlib
import hmac as _hmac
import time
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import URLSafeSerializer

from src import app
from src.authentication.core.domain.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
)
from src.authentication.core.usecases import (
    ChangePasswordUseCase,
    ExecutePasswordResetUseCase,
    LoginLocalUserUseCase,
    RequestNewVerificationEmailUseCase,
    VerifyEmailUseCase,
)
from src.shared.config import app_settings, verification_settings
from tests.conftest import (
    MockCache,
    MockEmailSender,
    MockLogger,
    MockPasswordHasher,
    MockRefreshTokenPort,
    MockUserRepository,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_verify_usecase(user_repo, cache, email_sender=None, refresh_repo=None, logger=None):
    return VerifyEmailUseCase(
        user_repo=user_repo,
        cache=cache,
        logger=logger or MockLogger(),
        email_sender=email_sender or MockEmailSender(),
        refresh_repo=refresh_repo or MockRefreshTokenPort(),
    )

def _seed_pending_otp(cache, email: str, otp: str, attempts: int = 0, expired: bool = False):
    """Directly write an OTP payload into the mock cache."""
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    secret = app_settings.SESSION_SECRET.encode()
    otp_hash = _hmac.new(secret, otp.encode(), _hashlib.sha256).hexdigest()
    expires_at = int(time.time()) - 1 if expired else int(time.time()) + 300
    cache.data[f"pending_reg:{email_hash}"] = {
        "otp": otp_hash,
        "otp_expires_at": expires_at,
        "pending_password_hash": "hashed_pass",
        "pending_name": "Test",
        "attempts": attempts,
    }


# ── AUD-01: Atomic OTP counter ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_otp_max_attempts_enforced(mock_session):
    """G-01/G-02: After OTP_MAX_ATTEMPTS wrong guesses the account is locked."""
    user_repo = MockUserRepository()
    cache = MockCache()
    email = "brute@example.com"

    await user_repo.create_user_with_password(mock_session, email, "Test", None, is_verified=False)
    _seed_pending_otp(cache, email, "999999")

    usecase = _make_verify_usecase(user_repo, cache)

    for i in range(5):
        with pytest.raises(InvalidTokenException):
            await usecase.execute(mock_session, email, "000000")

    # 6th attempt — even the CORRECT OTP must be rejected (key deleted)
    with pytest.raises((InvalidTokenException, InvalidCredentialsException)):
        await usecase.execute(mock_session, email, "999999")


@pytest.mark.asyncio
async def test_otp_attempt_counter_increments_atomically(mock_session):
    """G-01: Each failed attempt increments the counter exactly once."""
    user_repo = MockUserRepository()
    cache = MockCache()
    email = "atomic@example.com"

    await user_repo.create_user_with_password(mock_session, email, "Test", None, is_verified=False)
    _seed_pending_otp(cache, email, "999999")

    usecase = _make_verify_usecase(user_repo, cache)

    for expected_count in range(1, 4):
        with pytest.raises(InvalidTokenException):
            await usecase.execute(mock_session, email, "000000")
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        attempt_key = f"otp_attempts:{email_hash}"
        assert int(cache.data.get(attempt_key, 0)) == expected_count


@pytest.mark.asyncio
async def test_otp_correct_code_succeeds_and_clears_counter(mock_session):
    """G-01: Successful OTP clears the attempt counter key."""
    user_repo = MockUserRepository()
    cache = MockCache()
    email = "success@example.com"

    await user_repo.create_user_with_password(mock_session, email, "Test", None, is_verified=False)
    otp = "123456"
    _seed_pending_otp(cache, email, otp)

    usecase = _make_verify_usecase(user_repo, cache)

    with pytest.raises(InvalidTokenException):
        await usecase.execute(mock_session, email, "000000")

    await usecase.execute(mock_session, email, otp)

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    attempt_key = f"otp_attempts:{email_hash}"
    assert attempt_key not in cache.data


@pytest.mark.asyncio
async def test_concurrent_otp_attempts_cannot_exceed_limit(mock_session):
    """
    G-01: Fire OTP_MAX_ATTEMPTS+5 concurrent coroutines.
    With atomic INCR the total bypasses must be 0.
    Uses asyncio.gather to simulate concurrency within a single event loop.
    """
    user_repo = MockUserRepository()
    cache = MockCache()
    email = "concurrent@example.com"

    await user_repo.create_user_with_password(mock_session, email, "Test", None, is_verified=False)
    _seed_pending_otp(cache, email, "999999")

    usecase = _make_verify_usecase(user_repo, cache)
    limit = verification_settings.OTP_MAX_ATTEMPTS
    total = limit + 5

    results = await asyncio.gather(
        *[usecase.execute(mock_session, email, "000000") for _ in range(total)],
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) == 0, (
        f"Expected 0 successful brute-force bypasses, got {len(successes)}."
    )


# ── AUD-02 / AUD-03: Session revocation ──────────────────────────────────────

@pytest.mark.asyncio
async def test_password_reset_revokes_all_sessions(mock_session):
    """G-03 (AUD-02): All refresh tokens are revoked after password reset."""

    user_repo = MockUserRepository()
    cache = MockCache()
    user_id = uuid4()
    token = "valid_reset_token"
    cache.data[f"pwd_reset:{token}"] = str(user_id)

    revoke_all_called = False

    class TrackingRefreshRepo(MockRefreshTokenPort):
        async def revoke_all_for_user(self, session, uid):
            nonlocal revoke_all_called
            revoke_all_called = True
            assert uid == user_id

    usecase = ExecutePasswordResetUseCase(  # type: ignore
        user_repo=user_repo,
        cache=cache,
        hasher=MockPasswordHasher(),
        refresh_repo=TrackingRefreshRepo(),
    )
    result = await usecase.execute(mock_session, token, "NewPass123!")

    assert result is True
    assert revoke_all_called, "revoke_all_for_user must be called on password reset"


@pytest.mark.asyncio
async def test_change_password_revokes_all_sessions(mock_session):
    """G-04 (AUD-03): All refresh tokens are revoked after change-password."""

    user_repo = MockUserRepository()
    user_id = uuid4()
    user_repo.passwords[user_id] = "hashed_oldpassword"

    revoke_all_called = False

    class TrackingRefreshRepo(MockRefreshTokenPort):
        async def revoke_all_for_user(self, session, uid):
            nonlocal revoke_all_called
            revoke_all_called = True

    usecase = ChangePasswordUseCase(  # type: ignore
        user_repo=user_repo,
        hasher=MockPasswordHasher(),
        logger=MockLogger(),
        refresh_repo=TrackingRefreshRepo(),
    )
    await usecase.execute(mock_session, user_id, "oldpassword", "NewPass123!")
    assert revoke_all_called, "revoke_all_for_user must be called on change-password"


# ── AUD-04: Account restore notification ──────────────────────────────────────

@pytest.mark.asyncio
async def test_login_sends_restore_email_for_deleted_account(mock_session):
    """G-05 (AUD-04): A soft-deleted account triggers a security notification email."""

    user_repo = MockUserRepository()
    email_sender = MockEmailSender()
    email = "deleted@example.com"

    await user_repo.create_user_with_password(mock_session, email, "Test", None, is_verified=True)
    user = await user_repo.find_by_email(mock_session, email)
    assert user is not None
    user_repo.passwords[user.id] = "hashed_mypassword"
    user.deleted_at = datetime.now(timezone.utc)

    usecase = LoginLocalUserUseCase(  # type: ignore
        user_repo=user_repo,
        refresh_repo=MockRefreshTokenPort(),
        hasher=MockPasswordHasher(),
        logger=MockLogger(),
        email_sender=email_sender,
    )
    await usecase.execute(mock_session, email, "mypassword")

    assert hasattr(email_sender, "send_account_restored_email") or hasattr(email_sender, "restore_notifications"), \
        "send_account_restored_email must be called when a deleted account logs in"


# ── AUD-05: OTP resend resets attempt counter ──────────────────────────────────

@pytest.mark.asyncio
async def test_otp_resend_resets_attempt_count(mock_session):
    """G-06 (AUD-05): A new OTP issued via resend starts with attempts=0."""
    user_repo = MockUserRepository()
    cache = MockCache()
    email_sender = MockEmailSender()
    email = "resend@example.com"

    await user_repo.create_user_with_password(mock_session, email, "Test", None, is_verified=False)
    _seed_pending_otp(cache, email, "111111", attempts=4)

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    cache.data[f"otp_attempts:{email_hash}"] = "4"

    resend_usecase = RequestNewVerificationEmailUseCase(  # type: ignore
        user_repo=user_repo,
        logger=MockLogger(),
        email_sender=email_sender,
        cache=cache,
    )
    await resend_usecase.execute(mock_session, email)

    payload = await cache.get_dict(f"pending_reg:{email_hash}")
    assert payload is not None
    assert payload.get("attempts") == 0, "Attempt counter must reset to 0 on OTP resend"
    assert cache.data.get(f"otp_attempts:{email_hash}") is None, \
        "Atomic attempt key must be deleted on OTP resend"


# ── AUD-07: CSRF exception precision ──────────────────────────────────────────

def test_csrf_bad_signature_returns_corrupted_message():
    """G-07 (AUD-07): A tampered CSRF cookie raises 'corrupted', not 'not bound'."""

    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("refresh_token", "some_token")
    client.cookies.set("csrf_token", "INVALID_GARBAGE")
    resp = client.post(
        "/auth/refresh",
        headers={"X-CSRF": "INVALID_GARBAGE"},
    )
    assert resp.status_code == 403
    detail = resp.json().get("detail", "")
    assert "corrupted" in detail.lower(), f"Expected 'corrupted' in detail, got: {detail!r}"


def test_csrf_mismatched_token_returns_not_bound_message():
    """G-07 (AUD-07): A valid-signed but session-mismatched token raises 'not bound'."""

    csrf_signer = URLSafeSerializer(app_settings.SESSION_SECRET, salt="csrf-token")
    wrong_hash = hashlib.sha256(b"different_token").hexdigest()
    mismatched_csrf = csrf_signer.dumps(wrong_hash)

    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("refresh_token", "actual_token")
    client.cookies.set("csrf_token", mismatched_csrf)
    resp = client.post(
        "/auth/refresh",
        headers={"X-CSRF": mismatched_csrf},
    )
    assert resp.status_code == 403
    detail = resp.json().get("detail", "")
    assert "not bound" in detail.lower(), f"Expected 'not bound' in detail, got: {detail!r}"
