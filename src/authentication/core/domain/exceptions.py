"""
Module: Exceptions
"""
class AuthBaseException(Exception):
    status_code: int = 500
    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(message)

class EmailAlreadyRegisteredException(AuthBaseException):
    status_code: int = 409
    def __init__(self, message: str = "Email already registered"):
        super().__init__(message)

class InvalidCredentialsException(AuthBaseException):
    status_code: int = 401
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)

class UnverifiedEmailException(AuthBaseException):
    status_code: int = 403
    def __init__(self, message: str = "Please verify your email address before logging in"):
        super().__init__(message)

class InvalidTokenException(AuthBaseException):
    status_code: int = 401
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)

class NotAuthenticatedException(AuthBaseException):
    status_code: int = 401
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message)

class CSRFValidationException(AuthBaseException):
    status_code: int = 403
    def __init__(self, message: str = "CSRF validation failed"):
        super().__init__(message)

class InvalidProviderException(AuthBaseException):
    status_code: int = 400
    def __init__(self, message: str = "Invalid authentication provider"):
        super().__init__(message)

class OAuthFailedException(AuthBaseException):
    status_code: int = 400
    def __init__(self, message: str = "OAuth authentication failed"):
        super().__init__(message)

class SessionNotFoundException(AuthBaseException):
    status_code: int = 404
    def __init__(self, message: str = "Session not found or does not belong to user"):
        super().__init__(message)

class SamePasswordException(AuthBaseException):
    status_code: int = 400
    def __init__(self, message: str = "New password must be different from the current password"):
        super().__init__(message)
