"""
Dependency Injection Container (Composition Root)
This file is responsible for instantiating and wiring all singletons in the application.
By centralizing dependencies here, we avoid scattered "magic" registries while keeping
our core usecases purely dependent on interfaces (Ports).
"""

from src.shared.config import url_settings, email_settings, app_settings
from src.authentication.adapters.security.access_token import JWTAccessTokenAdapter
from src.authentication.adapters.repository.refresh_token_repository import DBRefreshTokenRepositoryAdapter

from src.authentication.adapters.repository.user_repository import SQLUserRepositoryAdapter
from src.authentication.core.usecases import (
    OAuthCallbackUseCase,
    RegisterLocalUserUseCase,
    LoginLocalUserUseCase,
    RequestPasswordResetUseCase,
    ExecutePasswordResetUseCase,
    RequestNewVerificationEmailUseCase,
    VerifyEmailUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
    ListSessionsUseCase,
    RevokeSessionUseCase
)
from src.authentication.core.usecases.change_password import ChangePasswordUseCase
from src.authentication.core.ports import ClaimsProviderPort
from src.shared.core.ports.cache import CachePort
from src.shared.infrastructure.sql.uow import SQLAlchemyUnitOfWork

from src.authentication.adapters.email_sender import AuthEmailService
from src.authentication.adapters.security.password_hasher import Argon2PasswordHasher
from src.shared.config import token_settings
from src.shared.adapters.logger import AsyncSQLLogger
from pathlib import Path
import threading


class Container:
    def __init__(self):
        # =====================================================================
        # 1. INFRASTRUCTURE ADAPTERS
        # =====================================================================
        self.access_token_adapter = JWTAccessTokenAdapter(
            private_key=app_settings.JWT_PRIVATE_KEY,
            public_key=app_settings.JWT_PUBLIC_KEY,
            lifetime_minutes=token_settings.ACCESS_TOKEN_LIFETIME_MINUTES,
        )

        from src.shared.container import shared_container
        
        self.cache_adapter: CachePort = shared_container.cache_adapter
        self.task_runner = shared_container.task_runner
        self.email_client = shared_container.email_client

        self.refresh_token_repo = DBRefreshTokenRepositoryAdapter(
            lifetime_days=token_settings.REFRESH_TOKEN_LIFETIME_DAYS,
            cache=self.cache_adapter,
        )

        self.email_sender = AuthEmailService(
            email_client=self.email_client,
            from_email=email_settings.FROM,
            templates_dir=Path(__file__).parent.parent.parent / "shared" / "templates" / "emails",
            logger=AsyncSQLLogger("EmailSender"),
            proj_name=app_settings.PROJECT_NAME,
            template_name=email_settings.TEMPLATE_NAME,
            frontend_url=url_settings.FRONTEND_URL,
            task_runner=self.task_runner,
        )

        self.user_repo = SQLUserRepositoryAdapter()
        self.password_hasher = Argon2PasswordHasher()

        # =====================================================================
        # 2. APPLICATION USE CASES
        # =====================================================================
        # --- AUTO-DISCOVERY PLUG-IN ---
        # The Authentication domain automatically checks if the Authorization domain 
        # has exported a custom claims provider for RBAC systems.
        try:
            from src.authorization.container import custom_claims_provider
            self.claims_provider: ClaimsProviderPort = custom_claims_provider # type: ignore
        except ImportError:
            # Fallback if the developer hasn't created one
            from src.authentication.adapters.security.claims_provider import NullClaimsProviderAdapter
            self.claims_provider = NullClaimsProviderAdapter()

        self.oauth_callback_usecase: OAuthCallbackUseCase[SQLAlchemyUnitOfWork] = OAuthCallbackUseCase(
            user_repo=self.user_repo,
            refresh_repo=self.refresh_token_repo,
            email_sender=self.email_sender,
        )

        self.register_local_usecase: RegisterLocalUserUseCase[SQLAlchemyUnitOfWork] = RegisterLocalUserUseCase(
            user_repo=self.user_repo,
            hasher=self.password_hasher,
            logger=AsyncSQLLogger("RegisterLocalUseCase"),
            email_sender=self.email_sender,
            cache=self.cache_adapter,
        )

        self.login_local_usecase: LoginLocalUserUseCase[SQLAlchemyUnitOfWork] = LoginLocalUserUseCase(
            user_repo=self.user_repo,
            refresh_repo=self.refresh_token_repo,
            hasher=self.password_hasher,
            logger=AsyncSQLLogger("LoginLocalUseCase"),
            email_sender=self.email_sender,
        )

        self.request_new_verification_email_usecase: RequestNewVerificationEmailUseCase[SQLAlchemyUnitOfWork] = RequestNewVerificationEmailUseCase(
            user_repo=self.user_repo,
            logger=AsyncSQLLogger("RequestNewVerificationEmailUseCase"),
            email_sender=self.email_sender,
            cache=self.cache_adapter,
        )

        self.verify_email_usecase: VerifyEmailUseCase[SQLAlchemyUnitOfWork] = VerifyEmailUseCase(
            user_repo=self.user_repo,
            cache=self.cache_adapter,
            logger=AsyncSQLLogger("VerifyEmailUseCase"),
            email_sender=self.email_sender,
            refresh_repo=self.refresh_token_repo,
        )

        self.logout_usecase: LogoutUseCase[SQLAlchemyUnitOfWork] = LogoutUseCase(
            refresh_repo=self.refresh_token_repo,
            cache=self.cache_adapter,
        )

        self.refresh_session_usecase: RefreshSessionUseCase[SQLAlchemyUnitOfWork] = RefreshSessionUseCase(
            refresh_repo=self.refresh_token_repo,
            access_token=self.access_token_adapter,
            claims_provider=self.claims_provider,
        )

        self.request_password_reset_usecase: RequestPasswordResetUseCase[SQLAlchemyUnitOfWork] = RequestPasswordResetUseCase(
            user_repo=self.user_repo,
            cache=self.cache_adapter,
            email_sender=self.email_sender,
            frontend_url=url_settings.FRONTEND_URL,
        )

        self.execute_password_reset_usecase: ExecutePasswordResetUseCase[SQLAlchemyUnitOfWork] = ExecutePasswordResetUseCase(
            user_repo=self.user_repo,
            cache=self.cache_adapter,
            hasher=self.password_hasher,
            refresh_repo=self.refresh_token_repo,
        )

        self.list_sessions_usecase: ListSessionsUseCase[SQLAlchemyUnitOfWork] = ListSessionsUseCase(
            refresh_repo=self.refresh_token_repo,
        )

        self.revoke_session_usecase: RevokeSessionUseCase[SQLAlchemyUnitOfWork] = RevokeSessionUseCase(
            refresh_repo=self.refresh_token_repo,
        )

        self.change_password_usecase: ChangePasswordUseCase[SQLAlchemyUnitOfWork] = ChangePasswordUseCase(
            user_repo=self.user_repo,
            hasher=self.password_hasher,
            logger=AsyncSQLLogger("ChangePasswordUseCase"),
            refresh_repo=self.refresh_token_repo,
        )

_container_instance = None
_container_lock = threading.Lock()

def get_container() -> Container:
    global _container_instance
    if _container_instance is None:
        with _container_lock:
            if _container_instance is None:
                _container_instance = Container()
    return _container_instance
