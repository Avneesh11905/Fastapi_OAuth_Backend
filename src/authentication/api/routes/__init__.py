from fastapi import APIRouter

from src.authentication.api.routes.callbacks import router as callback_router
from src.authentication.api.routes.local import router as local_router
from src.authentication.api.routes.logout import router as logout_router
from src.authentication.api.routes.oauth_login import router as login_router
from src.authentication.api.routes.refresh import router as refresh_router
from src.authentication.api.routes.reset_password import router as reset_password_router
from src.authentication.api.routes.sessions import router as sessions_router
from src.authentication.api.routes.verify_email import router as verify_email_router

auth_router = APIRouter(prefix='/auth', tags=['Auth'])
auth_router.include_router(login_router)
auth_router.include_router(logout_router)
auth_router.include_router(refresh_router)
auth_router.include_router(callback_router)
auth_router.include_router(local_router)
auth_router.include_router(reset_password_router)
auth_router.include_router(verify_email_router)
auth_router.include_router(sessions_router)
