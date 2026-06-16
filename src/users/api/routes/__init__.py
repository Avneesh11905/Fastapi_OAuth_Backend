from fastapi import APIRouter

from src.users.api.routes.profile import router as profile_router

users_router = APIRouter(prefix='/users', tags=['Users'])
users_router.include_router(profile_router)
