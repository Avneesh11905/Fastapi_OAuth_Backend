"""
Handles the core business logic for processing OAuth provider callbacks.
It implements an "Account Linking" strategy:
1. Exact match: If the provider's subject ID matches an existing linked account, log them in.
2. Email match: If the email matches an existing local/OAuth user, link this new provider to their account to avoid duplicate accounts.
3. Fallback: Create a brand new user.
"""
from src.shared.core.ports.uow import UoWPort
from typing import TYPE_CHECKING

from src.authentication.core.domain import UserIdentity
from src.authentication.core.domain.user import OAuthUserInfo

if TYPE_CHECKING:
    pass
from src.authentication.core.domain.session import ClientMetadata
from src.authentication.core.ports import RefreshTokenRepositoryPort, UserRepositoryPort
from src.authentication.core.ports.email_sender import EmailSenderPort


class OAuthCallbackUseCase[SessionType]:
    """
    Orchestrates the OAuth callback flow:
    1. Upsert user with account-linking (find by provider, email, or create new).
    2. Issue a refresh token for the session.

    Routes call this use case and handle HTTP response/cookie construction themselves.
    """

    def __init__(
        self,
        user_repo: "UserRepositoryPort",
        refresh_repo: "RefreshTokenRepositoryPort",
        email_sender: "EmailSenderPort",
    ):
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo
        self._email_sender = email_sender

    async def execute(self, uow: UoWPort[SessionType], user_info: OAuthUserInfo, client_meta: ClientMetadata | None = None) -> tuple[UserIdentity, str, bool]:
        """
        Process an OAuth callback.

        Args:
            session: Database session (injected by FastAPI dependency).
            user_info: Structured OAuth data payload from the provider.

        Returns:
            (user_identity, raw_refresh_token, is_new_user)
        """
        provider = user_info.provider
        oauth_sub = user_info.sub
        email = user_info.email
        name = user_info.name
        picture = user_info.picture

        # Step 1: Check if this exact provider+sub already exists
        user = await self._user_repo.find_by_oauth(uow.session, provider, oauth_sub)
        if user:
            if getattr(user, 'deleted_at', None) is not None:
                await self._user_repo.undelete_user(uow.session, user.id)
                user.deleted_at = None
                await self._email_sender.send_account_restored_email(user.email, user.name)
                
            # We explicitly DO NOT update the name/picture here so we don't overwrite user preferences
            refresh_token = await self._refresh_repo.create(uow.session, user.id, auth_provider=provider, client_meta=client_meta)
            return user, refresh_token, False

        # Step 2: Check if a user with this email already exists (account linking)
        user = await self._user_repo.find_by_email(uow.session, email)
        if user:
            # S3 Fix: Only link if the existing local account is verified.
            # If it's unverified, we shouldn't implicitly trust the email match,
            # but since OAuth providers usually verify emails, we can overwrite it or mark it verified.
            # To be safe, we only link if verified. If unverified, we could overwrite the password, 
            # but here we'll just link and mark verified to avoid hijack. 
            # Wait, actually, if it's unverified, Mallory could have registered it to hijack Alice's Google login. 
            # So if it's unverified, we should NOT link it to Mallory's unverified password.
            # However, the user_repo doesn't have an easy way to delete the password.
            # Let's just raise an error or delete the unverified user and create new.
            # For simplicity, if unverified, we'll mark as verified, but they can still log in locally if Mallory set the password.
            # To prevent hijack, we shouldn't let them log in locally if they were unverified.
            # We will just overwrite their password hash to something unusable.
            if not user.is_verified:
                await self._user_repo.disable_local_login(uow.session, user.id)
                await self._user_repo.verify_user_email(uow.session, user.id)

            if getattr(user, 'deleted_at', None) is not None:
                await self._user_repo.undelete_user(uow.session, user.id)
                user.deleted_at = None
                await self._email_sender.send_account_restored_email(user.email, user.name)

            await self._user_repo.link_oauth_account(uow.session, user.id, provider, oauth_sub)
            refresh_token = await self._refresh_repo.create(uow.session, user.id, auth_provider=provider, client_meta=client_meta)
            return user, refresh_token, False

        # Step 3: Brand new user
        user = await self._user_repo.create_user_with_oauth(
            uow.session, email, name, str(picture) if picture else None, provider, oauth_sub,
        )
        refresh_token = await self._refresh_repo.create(uow.session, user.id, auth_provider=provider, client_meta=client_meta)
        
        # Fire-and-forget email sending
        await self._email_sender.send_welcome_email(user.email, user.name)
        
        return user, refresh_token, True
