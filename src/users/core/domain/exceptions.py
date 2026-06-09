class UserBaseException(Exception):
    status_code: int = 500
    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(message)

class UserNotFoundException(UserBaseException):
    status_code: int = 404
    def __init__(self, message: str = "User not found"):
        super().__init__(message)
