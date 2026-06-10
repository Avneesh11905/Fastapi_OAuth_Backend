class UserBaseException(Exception):
    status_code: int = 500
    def __init__(self, detail: str = "Internal Server Error"):
        super().__init__(detail)

class UserNotFoundException(UserBaseException):
    status_code: int = 404
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail)
