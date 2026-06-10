import pytest
from uuid import uuid4
from src.authentication.core.domain import UserIdentity

class MockUserRepository:
    def __init__(self):
        self.users = {}  # id -> UserIdentity
        self.oauth_links = [] # tuple (user_id, provider, oauth_sub)
        self.passwords = {} # user_id -> hash

    async def find_by_oauth(self, session, provider: str, oauth_sub: str) -> UserIdentity | None:
        for link in self.oauth_links:
            if link[1] == provider and link[2] == oauth_sub:
                return self.users[link[0]]
        return None

    async def find_by_email(self, session, email: str) -> UserIdentity | None:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def create_user_with_oauth(
        self, session, email: str, name: str | None, picture: str | None,
        provider: str, oauth_sub: str,
    ) -> UserIdentity:
        user_id = str(uuid4())
        user = UserIdentity(id=user_id, email=email, name=name, picture=picture, is_verified=True)
        self.users[user_id] = user
        self.oauth_links.append((user_id, provider, oauth_sub))
        return user

    async def link_oauth_account(
        self, session, user_id: str, provider: str, oauth_sub: str,
    ) -> None:
        self.oauth_links.append((user_id, provider, oauth_sub))

    async def create_user_with_password(
        self, session, email: str, name: str | None, password_hash: str, is_verified: bool = False
    ) -> UserIdentity:
        user_id = str(uuid4())
        user = UserIdentity(id=user_id, email=email, name=name, is_verified=is_verified)
        self.users[user_id] = user
        self.passwords[user_id] = password_hash
        return user

    async def find_password_hash(self, session, user_id: str) -> str | None:
        return self.passwords.get(user_id)

    async def disable_local_login(self, session, user_id: str) -> None:
        if user_id in self.passwords:
            del self.passwords[user_id]

    async def verify_user_email(self, session, user_id: str) -> None:
        user = self.users[user_id]
        updated_user = UserIdentity(
            id=user.id,
            email=user.email,
            is_verified=True,
            name=user.name,
            picture=user.picture
        )
        self.users[user_id] = updated_user

    async def update_password(self, session, user_id: str, new_password_hash: str) -> None:
        self.passwords[user_id] = new_password_hash

class MockEmailSender:
    def __init__(self):
        self.sent_otps = {}

    async def send_welcome_email(self, to_email: str, name: str | None): pass
    async def send_password_reset_email(self, to_email: str, reset_url: str): pass
    async def send_verification_email(self, to_email: str, otp: str): 
        self.sent_otps[to_email] = otp

class MockCache:
    def __init__(self):
        self.data = {}
        
    async def set_string(self, key: str, value: str, ttl_seconds: int): 
        self.data[key] = value
        
    async def get_string(self, key: str): 
        return self.data.get(key)
    
    async def set_dict(self, key: str, data: dict, ttl: int): 
        self.data[key] = data
        
    async def get_dict(self, key: str) -> dict | None: 
        return self.data.get(key)
        
    async def delete_key(self, key: str): 
        if key in self.data:
            del self.data[key]

    async def incr(self, key: str) -> int:
        if key not in self.data:
            self.data[key] = "1"
            return 1
        else:
            val = int(self.data[key]) + 1
            self.data[key] = str(val)
            return val


class MockRefreshTokenPort:
    async def create(self, session, user_id: str, auth_provider: str = "local", client_meta=None) -> str:
        return f"mock_token_for_{user_id}"

    async def validate(self, session, token: str, client_meta=None) -> tuple[UserIdentity | None, str | None, str | None]:
        return None, None, None

    async def revoke(self, session, token: str) -> None:
        pass

    async def revoke_by_family(self, session, family_id: str) -> None:
        pass

    async def get_active_sessions(self, session, user_id: str, current_token: str | None = None) -> list:
        return []

    async def cleanup_expired(self, session) -> int:
        return 0


class MockPasswordHasher:
    async def hash_password(self, password: str) -> str:
        return f"hashed_{password}"

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed_{password}"


class MockLogger:
    async def info(self, msg: str): pass
    async def warning(self, msg: str): pass
    async def error(self, msg: str): pass
    async def fatal(self, msg: str): pass
    async def debug(self, msg: str): pass
    async def trace(self, msg: str): pass


@pytest.fixture
def user_repo():
    return MockUserRepository()

@pytest.fixture
def refresh_token_port():
    return MockRefreshTokenPort()

@pytest.fixture
def password_hasher():
    return MockPasswordHasher()

@pytest.fixture
def logger_port():
    return MockLogger()

@pytest.fixture
def mock_session():
    class DummySession:
        pass
    return DummySession()
