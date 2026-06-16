"""
Provides secure, one-way cryptographic hashing for passwords using Argon2id.
Argon2id is currently the OWASP recommended algorithm because it resists both GPU cracking and side-channel timing attacks.
"""
import asyncio

from passlib.context import CryptContext  # type: ignore


class Argon2PasswordHasher:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["argon2"], 
                                        deprecated="auto",
                                        argon2__time_cost=3,
                                        argon2__memory_cost=65536,  # 64 MB
                                        argon2__parallelism=2)
        
    async def hash_password(self, password: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.pwd_context.hash, password)

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.pwd_context.verify, password, hashed_password)

    async def dummy_verify(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.pwd_context.dummy_verify)
    
