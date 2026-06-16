import hashlib
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient
from itsdangerous import URLSafeSerializer
from limits.storage import MemoryStorage

import src.authentication.infrastructure.oauth as oauth_infra
from src import app
from src.authentication.api import usecase_dependencies as deps
from src.authentication.api.dependencies import get_current_user, get_jwt_payload
from src.authentication.core.domain.user import UserIdentity
from src.authorization.api.dependencies import require_permission, require_role
from src.authorization.container import custom_claims_provider
from src.shared.api.dependencies import limiter
from src.shared.config import app_settings, rate_limit_settings
from src.shared.infrastructure.sql.connection import get_db
from src.users.core.domain.profile import UserProfile


def _get_valid_csrf(refresh_token: str) -> str:
    csrf_signer = URLSafeSerializer(app_settings.SESSION_SECRET, salt="csrf-token")
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    return csrf_signer.dumps(refresh_token_hash)


limiter.enabled = False
rate_limit_settings.LOGIN_RATE_LIMIT = "1000/minute"
rate_limit_settings.DEFAULT_RATE_LIMIT = "1000/minute"

@pytest.fixture(scope="module")
def mock_usecases():
    class MockUseCase:
        async def execute(self, *args, **kwargs):
            return "mocked_response"
            
    class MockLoginUseCase:
        async def execute(self, *args, **kwargs):
            # return user, refresh_token
            class MockUser:
                id = "123"
            return MockUser(), "mock_refresh_token"

    class MockOAuthCallbackUseCase:
        async def execute(self, *args, **kwargs):
            # return user, refresh_token, is_new_user
            class MockUser:
                id = "123"
            return MockUser(), "mock_refresh_token", True
            
    class MockExecutePasswordResetUseCase:
        async def execute(self, *args, **kwargs):
            token = kwargs.get("token") or (args[1] if len(args) > 1 else None)
            if token == "nonexistent_token":
                return False
            return True

    class MockLogoutUseCase:
        async def execute(self, *args, **kwargs):
            pass

    class MockRefreshUseCase:
        async def execute(self, *args, **kwargs):
            return "new_access_token", "new_refresh_token"

    class MockListSessionsUseCase:
        async def execute(self, *args, **kwargs):
            return []

    class MockRevokeSessionUseCase:
        async def execute(self, *args, **kwargs):
            pass

    return {
        deps.get_register_local_usecase: MockUseCase(),
        deps.get_login_local_usecase: MockLoginUseCase(),
        deps.get_oauth_callback_usecase: MockOAuthCallbackUseCase(),
        deps.get_refresh_session_usecase: MockRefreshUseCase(),
        deps.get_request_new_verification_email_usecase: MockUseCase(),
        deps.get_verify_email_usecase: MockLoginUseCase(),
        deps.get_request_password_reset_usecase: MockUseCase(),
        deps.get_execute_password_reset_usecase: MockExecutePasswordResetUseCase(),
        deps.get_logout_usecase: MockLogoutUseCase(),
        deps.get_list_sessions_usecase: MockListSessionsUseCase(),
        deps.get_revoke_session_usecase: MockRevokeSessionUseCase(),
    }

@pytest.fixture(scope="module")
def test_client(mock_usecases):
    """Provides a TestClient with overridden UseCases to isolate router testing."""
    class DummySession:
        async def commit(self):
            pass

    app.dependency_overrides[get_db] = lambda: DummySession()
    mock_id = uuid.UUID('12345678-1234-5678-1234-567812345678')
    app.dependency_overrides[get_current_user] = lambda: UserIdentity(id=mock_id, email="test@test.com", is_verified=True)
    app.dependency_overrides[get_jwt_payload] = lambda: {"jti": "mock_jti", "exp": 9999999999, "_user_obj": UserIdentity(id=mock_id, email="test@test.com", is_verified=True)}
    
    for dep, mock_obj in mock_usecases.items():
        app.dependency_overrides[dep] = lambda mock_obj=mock_obj: mock_obj
        
    # Mocking profile repo and oauth clients
    
    mock_profile_repo = AsyncMock()
    mock_profile = UserProfile(id="123", email="test@test.com", name="Test", picture=None, receive_updates=False, login_methods=["local"])
    mock_profile_repo.get_profile.return_value = mock_profile
    mock_profile_repo.update_profile.return_value = mock_profile
    
    class MockOAuthClient:
        async def authorize_redirect(self, request: Request, redirect_uri: str, **kwargs) -> object:
            return RedirectResponse("https://provider.com/auth")
        async def authorize_access_token(self, request: Request, **kwargs) -> dict[str, object]:
            return {"token": "mock_token"}
            
    oauth_infra.PROVIDERS["google"] = MockOAuthClient()
    oauth_infra.PARSERS["google"] = AsyncMock(return_value=None)
    
    with patch("src.users.api.routes.profile.user_profile_repository", mock_profile_repo), \
         patch("src.__init__.start_log_worker_task", new_callable=AsyncMock), \
         patch("src.__init__.start_token_cleanup_task"), \
         patch("src.__init__.start_log_cleanup_task"), \
         patch("src.__init__.stop_token_cleanup_task"), \
         patch("src.__init__.stop_log_cleanup_task"):
        with TestClient(app) as client:
            yield client
        
    app.dependency_overrides.clear()


def test_register_local(test_client):
    response = test_client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "StrongPassword123!", "name": "Test User"}
    )
    assert response.status_code == 201
    assert "message" in response.json()

def test_login_local(test_client):
    response = test_client.post(
        "/auth/login/local",
        json={"email": "test@example.com", "password": "StrongPassword123!"}
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "refresh_token" in response.cookies

def test_verify_email(test_client):
    response = test_client.post(
        "/auth/verify-email",
        json={"email": "test@example.com", "otp": "123456"}
    )
    assert response.status_code == 200

def test_request_password_reset(test_client):
    response = test_client.post(
        "/auth/password/forgot",
        json={"email": "test@example.com"}
    )
    assert response.status_code == 200

def test_execute_password_reset(test_client):
    response = test_client.post(
        "/auth/password/reset",
        json={"token": "reset_token_123", "new_password": "NewStrongPassword123!"}
    )
    assert response.status_code == 200

def test_logout(test_client):
    test_client.cookies.set("refresh_token", "mock_refresh_token")
    test_client.cookies.set("csrf_token", _get_valid_csrf("mock_refresh_token"))
    response = test_client.post(
        "/auth/logout",
        headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")},
        follow_redirects=False
    )
    assert response.status_code == 200

def test_oauth_login_redirect(test_client):
    response = test_client.get(
        "/auth/login/google", 
        follow_redirects=False,
        headers={"X-Forwarded-For": str(uuid.uuid4())}
    )
    assert response.status_code == 307
    assert "provider.com" in response.headers["location"]

def test_oauth_callback(test_client):
    response = test_client.get("/auth/callback/google", follow_redirects=False)
    assert response.status_code == 307
    assert "refresh_token" in response.cookies

def test_refresh_token(test_client):
    test_client.cookies.set("refresh_token", "mock_refresh_token")
    test_client.cookies.set("csrf_token", _get_valid_csrf("mock_refresh_token"))
    response = test_client.post(
        "/auth/refresh", 
        headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_list_sessions(test_client):
    response = test_client.get("/auth/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_revoke_session(test_client):
    response = test_client.delete("/auth/sessions/12345678-1234-5678-1234-567812345678")
    assert response.status_code == 204

def test_get_profile(test_client):
    response = test_client.get("/users/me")
    assert response.status_code == 200
    assert response.json()["name"] == "Test"

def test_update_profile(test_client):
    test_client.cookies.set("csrf_token", _get_valid_csrf("mock_refresh_token"))
    response = test_client.patch(
        "/users/me",
        json={"name": "New Test"},
        headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test"

def test_update_profile_receive_updates(test_client):
    test_client.cookies.set("csrf_token", _get_valid_csrf("mock_refresh_token"))
    response = test_client.patch(
        "/users/me",
        json={"receive_updates": True},
        headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")}
    )
    assert response.status_code == 200

def test_delete_me(test_client):
    test_client.cookies.set("csrf_token", _get_valid_csrf("mock_refresh_token"))
    response = test_client.delete("/users/me", headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")})
    assert response.status_code == 204

def test_rate_limiting(test_client):
    original_storage = limiter._storage
    limiter._storage = MemoryStorage()
    limiter.enabled = True
    try:
        # The /auth/login/google endpoint has a 5/minute limit.
        # Keep hitting it until we hit the rate limit (429).
        # Use a unique IP to avoid affecting other test runs stored in Redis.
        headers = {"X-Forwarded-For": "9.9.9.9"}
        for _ in range(10):
            response = test_client.get("/auth/login/google", follow_redirects=False, headers=headers)
            if response.status_code == 429:
                break
        assert response.status_code == 429
    finally:
        limiter.enabled = False
        limiter._storage = original_storage

def test_authorization_dependencies(test_client):

    # Add a dummy protected route to the test app
    @test_client.app.get("/test/admin-only", dependencies=[Depends(require_role("admin"))])
    def admin_only():
        return {"msg": "ok"}
        
    @test_client.app.get("/test/write-doc", dependencies=[Depends(require_permission("write", "document"))])
    def write_doc():
        return {"msg": "ok"}

    # Mock the current JWT payload for roles
    
    # 1. Test role missing
    test_client.app.dependency_overrides[get_jwt_payload] = lambda: {"roles": ["user"], "sub": "123"}
    resp = test_client.get("/test/admin-only", headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")})
    assert resp.status_code == 403
    
    # 2. Test role present
    test_client.app.dependency_overrides[get_jwt_payload] = lambda: {"roles": ["user", "admin"], "sub": "123"}
    resp = test_client.get("/test/admin-only", headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")})
    assert resp.status_code == 200
    
    # 3. Test permission missing (default deny)
    # The default CustomAuthorizationAdapter returns False
    resp = test_client.get("/test/write-doc", headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")})
    assert resp.status_code == 403
    
    # 4. Test permission present
    with patch.object(custom_claims_provider, "has_permission", new_callable=AsyncMock, return_value=True):
        resp = test_client.get("/test/write-doc", headers={"X-CSRF": _get_valid_csrf("mock_refresh_token")})
        assert resp.status_code == 200


def test_register_rejects_weak_password(test_client):
    """Password shorter than 8 chars must return 422 Unprocessable Entity."""
    resp = test_client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "short", "name": "User"}
    )
    assert resp.status_code == 422


def test_register_rejects_invalid_email(test_client):
    """Malformed email must return 422."""
    resp = test_client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "StrongPass123!", "name": "User"}
    )
    assert resp.status_code == 422


def test_refresh_without_cookie_returns_204(test_client):
    """Missing refresh token cookie must return 204 No Content, not 500."""
    test_client.cookies.clear()
    test_client.cookies.set("csrf_token", "anything")
    resp = test_client.post(
        "/auth/refresh",
        headers={"X-CSRF": "anything"},
    )
    assert resp.status_code == 204


def test_protected_endpoint_without_bearer_returns_401(test_client):
    """Requests to protected endpoints with no Authorization header -> 401."""
    saved = test_client.app.dependency_overrides.pop(get_jwt_payload, None)
    saved2 = test_client.app.dependency_overrides.pop(get_current_user, None)
    try:
        resp = test_client.get("/auth/sessions")
        assert resp.status_code == 401
    finally:
        if saved:
            test_client.app.dependency_overrides[get_jwt_payload] = saved
        if saved2:
            test_client.app.dependency_overrides[get_current_user] = saved2


def test_password_reset_invalid_token_returns_400(test_client):
    """An invalid reset token must return 400, not 500."""
    resp = test_client.post(
        "/auth/password/reset",
        json={"token": "nonexistent_token", "new_password": "NewPass123!"}
    )
    assert resp.status_code == 400


def test_revoke_session_invalid_uuid_returns_422(test_client):
    """Passing a non-UUID family_id path param must return 422."""
    resp = test_client.delete("/auth/sessions/not-a-uuid")
    assert resp.status_code == 422


def test_csrf_missing_header_returns_403(test_client):
    """A CSRF-protected endpoint with no X-CSRF header must return 403."""
    resp = test_client.post("/auth/logout")
    assert resp.status_code == 403

