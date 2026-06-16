"""
Provides FastAPI dependencies for route-level access control.
You can import these and use them in your `Depends()` list.
"""
from typing import Annotated, Callable

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.authentication.api.dependencies import get_jwt_payload
from src.authorization.container import custom_claims_provider
from src.shared.infrastructure.sql.connection import get_db


def require_role(required_role: str) -> Callable:
    """
    Dependency factory that restricts access based on a stateless JWT role check.
    
    It parses the `roles` list from the user's JWT payload. Because the roles are encoded
    directly into the JWT upon login/refresh, this check is extremely fast and avoids
    hitting the database.
    """
    async def role_checker(payload: Annotated[dict, Depends(get_jwt_payload)]) -> dict:
        roles = payload.get("roles", [])
        if required_role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
        return payload
    return role_checker

def require_permission(action: str, resource: str) -> Callable:
    """
    Dependency factory that restricts access based on a stateful permissions check.
    
    It delegates to the `CustomAuthorizationAdapter.has_permission` method to execute 
    database-driven business rules (e.g., checking specific resource ownership or granular PBAC).
    """
    async def permission_checker(
        payload: Annotated[dict, Depends(get_jwt_payload)],
        db: Annotated[AsyncSession, Depends(get_db)]
    ) -> dict:
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized: Missing subject in token")
            
        has_access = await custom_claims_provider.has_permission(db, user_id, action, resource)
        if not has_access:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient permissions")
        return payload
    return permission_checker
