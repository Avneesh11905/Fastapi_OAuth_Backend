from sqlalchemy.ext.asyncio import AsyncSession

from src.authorization.core.ports.authorization_service import AuthorizationPort


class CustomAuthorizationAdapter(AuthorizationPort[AsyncSession]):
    """
    Your universal authorization implementation.
    
    This is where you should implement your business rules for RBAC, ABAC, etc.
    You have full access to the database session here, so you can look up
    roles, permissions, subscriptions, and quotas.
    """

    async def has_permission(self, session: AsyncSession, user_id: str, action: str, resource: str) -> bool:
        """
        Evaluate if a user can perform 'action' on 'resource'.
        This is called dynamically by the `Depends(require_permission(action, resource))` endpoint dependency.
        
        Example:
            if action == 'write' and resource == 'admin_panel':
                # db lookup to see if user has 'admin' role
                return await self._check_admin_role(session, user_id)
        """
        # Default fallback: default-deny in production!
        return False

    async def get_custom_claims(self, session: AsyncSession, user_id: str) -> dict:
        """
        Return a dictionary of claims to inject into the JWT upon login or refresh.
        This enables stateless authorization checks using the `Depends(require_role(role))` dependency.
        
        Example:
            roles = await self._fetch_user_roles(session, user_id)
            return {"roles": roles, "subscription": "pro"}
        """
        # Default fallback: inject a standard 'user' role
        return {"roles": ["user"]}
