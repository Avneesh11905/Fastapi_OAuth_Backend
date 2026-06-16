from pydantic import BaseModel


class Role(BaseModel):
    name: str
    description: str | None = None

class Permission(BaseModel):
    action: str
    resource: str

class UserAuthorizationContext(BaseModel):
    user_id: str
    roles: list[Role]
    permissions: list[Permission]
