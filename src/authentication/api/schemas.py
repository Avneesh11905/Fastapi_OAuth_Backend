"""
Module: Schemas
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from uuid import UUID

class _EmailMixin(BaseModel):
    @field_validator("email", mode="before", check_fields=False)
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v

class RegisterRequest(_EmailMixin):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str | None = None

class LoginRequest(_EmailMixin):
    email: EmailStr
    password: str = Field(..., max_length=128)

class ChangePasswordRequest(BaseModel):
    current_password: str | None = Field(default=None, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

class ForgotPasswordRequest(_EmailMixin):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

class VerifyEmailRequest(_EmailMixin):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class RequestNewVerificationEmail(_EmailMixin):
    email: EmailStr

class MessageResponse(BaseModel):
    message: str

class SessionResponse(BaseModel):
    family_id: UUID
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_active: datetime
    is_current: bool
    auth_provider: str
