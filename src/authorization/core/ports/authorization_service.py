from typing import Protocol


class AuthorizationPort[SessionType](Protocol):
    """
    Interface for handling Authorization (RBAC, ABAC, PBAC).
    This serves as a boilerplate boundary where you can plug in your own
    custom business logic to govern who can do what.
    """

    async def has_permission(self, session: SessionType, user_id: str, action: str, resource: str) -> bool:
        """
        Check if a user is allowed to perform a specific action on a specific resource.
        Example: has_permission(session, user_id, "read", "document:123")
        """
        ...
        
    async def get_custom_claims(self, session: SessionType, user_id: str) -> dict:
        """
        Retrieve the custom payload dictionary (like 'roles' or 'permissions') 
        that should be injected into the user's JWT Access Token.
        """
        ...
