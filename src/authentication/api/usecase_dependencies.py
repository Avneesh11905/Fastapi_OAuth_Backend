"""
FastAPI Dependency Injection for Use Cases.

This module provides FastAPI `Depends()`-compatible getter functions for all Use Cases.
By using these functions in the router layer, developers can leverage FastAPI's native
`app.dependency_overrides` mechanism to mock Use Cases during testing, bridging the gap
between Hexagonal Architecture and the FastAPI ecosystem.
"""
from src.authentication.container import get_container
from src.authentication.core.usecases import (
    RegisterLocalUserUseCase,
    LoginLocalUserUseCase,
    OAuthCallbackUseCase,
    RequestNewVerificationEmailUseCase,
    VerifyEmailUseCase,
    RequestPasswordResetUseCase,
    ExecutePasswordResetUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
    ListSessionsUseCase,
    RevokeSessionUseCase
)

from src.authentication.core.usecases.change_password import ChangePasswordUseCase

def get_register_local_usecase() -> RegisterLocalUserUseCase:
    return get_container().register_local_usecase

def get_login_local_usecase() -> LoginLocalUserUseCase:
    return get_container().login_local_usecase

def get_change_password_usecase() -> ChangePasswordUseCase:
    return get_container().change_password_usecase

def get_oauth_callback_usecase() -> OAuthCallbackUseCase:
    return get_container().oauth_callback_usecase

def get_request_new_verification_email_usecase() -> RequestNewVerificationEmailUseCase:
    return get_container().request_new_verification_email_usecase

def get_verify_email_usecase() -> VerifyEmailUseCase:
    return get_container().verify_email_usecase

def get_request_password_reset_usecase() -> RequestPasswordResetUseCase:
    return get_container().request_password_reset_usecase

def get_execute_password_reset_usecase() -> ExecutePasswordResetUseCase:
    return get_container().execute_password_reset_usecase

def get_logout_usecase() -> LogoutUseCase:
    return get_container().logout_usecase

def get_refresh_session_usecase() -> RefreshSessionUseCase:
    return get_container().refresh_session_usecase

def get_list_sessions_usecase() -> ListSessionsUseCase:
    return get_container().list_sessions_usecase

def get_revoke_session_usecase() -> RevokeSessionUseCase:
    return get_container().revoke_session_usecase
