"""
Module: Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str | None = None
    new_password: str = Field(min_length=8)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class RequestNewVerificationEmail(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    message: str

class SessionResponse(BaseModel):
    family_id: str
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_active: datetime
    is_current: bool
    auth_provider: str
