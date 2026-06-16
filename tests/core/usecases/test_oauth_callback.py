import pytest
from src.authentication.core.usecases import OAuthCallbackUseCase
from src.authentication.core.domain.user import OAuthUserInfo
from unittest.mock import AsyncMock
from pydantic import AnyHttpUrl
from typing import cast

@pytest.mark.asyncio
async def test_brand_new_user_signup(user_repo, refresh_token_port, mock_session):
    email_sender = AsyncMock()
    usecase: OAuthCallbackUseCase = OAuthCallbackUseCase(user_repo=user_repo, refresh_repo=refresh_token_port, email_sender=email_sender)
    
    from pydantic import AnyHttpUrl
    from typing import cast
    user_info = OAuthUserInfo(
        provider="google",
        sub="google_123",
        email="test@example.com",
        name="Test User",
        picture=cast(AnyHttpUrl, "https://example.com/pic.png")
    )

    user, token = await usecase.execute(mock_session, user_info)

    # Asserts
    email_sender.send_welcome_email.assert_called_once_with("test@example.com", "Test User")
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert token == f"mock_token_for_{user.id}"
    
    # Verify mock state
    assert len(user_repo.users) == 1
    assert len(user_repo.oauth_links) == 1

@pytest.mark.asyncio
async def test_existing_user_exact_oauth_match(user_repo, refresh_token_port, mock_session):
    # Pre-seed the DB
    await user_repo.create_user_with_oauth(
        mock_session, "test@example.com", "Old Name", None, "google", "google_123"
    )

    email_sender = AsyncMock()
    usecase: OAuthCallbackUseCase = OAuthCallbackUseCase(user_repo=user_repo, refresh_repo=refresh_token_port, email_sender=email_sender)
    
    # Login again with same provider/sub, but updated profile data
    user_info = OAuthUserInfo(
        provider="google",
        sub="google_123",
        email="test@example.com",
        name="New Name",
        picture=cast(AnyHttpUrl, "http://example.com/newpic.png")
    )

    user, token = await usecase.execute(mock_session, user_info)

    # Asserts
    email_sender.send_welcome_email.assert_not_called()
    assert user.name == "Old Name"  # Profile should NOT be overwritten on login
    assert user.picture is None
    assert len(user_repo.users) == 1 # Still only 1 user
    assert len(user_repo.oauth_links) == 1 # Still only 1 link

@pytest.mark.asyncio
async def test_account_linking_different_provider_same_email(user_repo, refresh_token_port, mock_session):
    # Pre-seed the DB with Google
    original_user = await user_repo.create_user_with_oauth(
        mock_session, "test@example.com", "Test User", "https://example.com/pic.png", "google", "google_123"
    )

    email_sender = AsyncMock()
    usecase: OAuthCallbackUseCase = OAuthCallbackUseCase(user_repo=user_repo, refresh_repo=refresh_token_port, email_sender=email_sender)
    
    # Login with GitHub but SAME email
    user_info = OAuthUserInfo(
        provider="github",
        sub="github_456",
        email="test@example.com",
        name=None, # GitHub doesn't provide a name
        picture=cast(AnyHttpUrl, "https://example.com/github.png")
    )

    user, token = await usecase.execute(mock_session, user_info)

    # Asserts
    email_sender.send_welcome_email.assert_not_called()
    assert user.id == original_user.id  # Same user!
    assert user.name == "Test User" # Fallback to existing name
    
    # Verify mock state
    assert len(user_repo.users) == 1 # Did NOT create a new user
    assert len(user_repo.oauth_links) == 2 # Did create a second oauth link
