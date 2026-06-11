"""
Defines a global hierarchy for Domain Exceptions.
These custom exceptions abstract away HTTP status codes from the core business logic.
The API layer catches them and translates them into appropriate HTTP responses.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.shared.adapters.logger import AsyncSQLLogger
from typing import Any

from src.authentication.core.domain.exceptions import AuthBaseException
from src.users.core.domain.exceptions import UserBaseException

logger = AsyncSQLLogger("ExceptionHandlers")

def build_error_response(status_code: int, detail: str | list[dict[str, Any]]) -> JSONResponse:
    """Helper to build a consistent JSON error response format matching FastAPI standards."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail}
    )

async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles standard HTTP Exceptions raised in the application."""
    await logger.error(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return build_error_response(exc.status_code, str(exc.detail))

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic validation errors nicely."""
    errors: list[dict[str, Any]] = []
    for err in exc.errors():
        errors.append({
            "loc": " -> ".join([str(loc) for loc in err.get("loc", [])]),
            "msg": err.get("msg"),
            "type": err.get("type")
        })
    await logger.warning(f"Validation Error at {request.url.path}: {errors}")
    return build_error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, errors)

async def auth_domain_exception_handler(request: Request, exc: AuthBaseException) -> JSONResponse:
    """Handles all auth-related Domain Exceptions gracefully by dynamically reading their status code."""
    code = getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST)
    await logger.warning(f"Domain Error ({exc.__class__.__name__}) at {request.url.path}: {str(exc)}")
    return build_error_response(code, str(exc))

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all unexpected crashes/exceptions."""
    await logger.error(f"Unhandled Exception at {request.url.path}: {str(exc)}")
    return build_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error")

async def user_domain_exception_handler(request: Request, exc: UserBaseException) -> JSONResponse:
    """Handles all user-related Domain Exceptions."""
    code = getattr(exc, "status_code", status.HTTP_404_NOT_FOUND)
    await logger.warning(f"User Error ({exc.__class__.__name__}) at {request.url.path}: {str(exc)}")
    return build_error_response(code, str(exc))

def register_exception_handlers(app: FastAPI):
    """Registers exception handlers for the FastAPI app."""
    app.add_exception_handler(StarletteHTTPException, custom_http_exception_handler) # type: ignore
    app.add_exception_handler(RequestValidationError, validation_exception_handler) # type: ignore
    app.add_exception_handler(AuthBaseException, auth_domain_exception_handler) # type: ignore
    app.add_exception_handler(UserBaseException, user_domain_exception_handler) # type: ignore
    app.add_exception_handler(Exception, global_exception_handler)
