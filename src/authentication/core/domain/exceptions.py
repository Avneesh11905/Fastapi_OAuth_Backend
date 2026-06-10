"""
Module: Exceptions
"""
class AuthBaseException(Exception):
    status_code: int = 500
    def __init__(self, detail: str = "Internal Server Error"):
        super().__init__(detail)

class EmailAlreadyRegisteredException(AuthBaseException):
    status_code: int = 409
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(detail)

class InvalidCredentialsException(AuthBaseException):
    status_code: int = 401
    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(detail)

class UnverifiedEmailException(AuthBaseException):
    status_code: int = 403
    def __init__(self, detail: str = "Please verify your email address before logging in"):
        super().__init__(detail)

class InvalidTokenException(AuthBaseException):
    status_code: int = 401
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(detail)

class NotAuthenticatedException(AuthBaseException):
    status_code: int = 401
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(detail)

class CSRFValidationException(AuthBaseException):
    status_code: int = 403
    def __init__(self, detail: str = "CSRF validation failed"):
        super().__init__(detail)

class InvalidProviderException(AuthBaseException):
    status_code: int = 400
    def __init__(self, detail: str = "Invalid authentication provider"):
        super().__init__(detail)

class OAuthFailedException(AuthBaseException):
    status_code: int = 400
    def __init__(self, detail: str = "OAuth authentication failed"):
        super().__init__(detail)

class SessionNotFoundException(AuthBaseException):
    status_code: int = 404
    def __init__(self, detail: str = "Session not found or does not belong to user"):
        super().__init__(detail)

class SamePasswordException(AuthBaseException):
    status_code: int = 400
    def __init__(self, detail: str = "New password must be different from the current password"):
        super().__init__(detail)
