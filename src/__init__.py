from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.authentication.api.routes import auth_router
from src.authentication.infrastructure.tasks import (
    start_token_cleanup_task,
    start_user_cleanup_task,
    stop_token_cleanup_task,
    stop_user_cleanup_task,
)
from src.shared.adapters.logger import (
    AsyncSQLLogger,
    start_log_worker_task,
    stop_log_worker_task,
)
from src.shared.api.dependencies import limiter
from src.shared.api.routes.debug_email import router as debug_email_router
from src.shared.api.routes.health import router as health_router
from src.shared.config import (
    app_settings,
)
from src.shared.core.exceptions import register_exception_handlers
from src.shared.infrastructure.tasks import (
    start_log_cleanup_task,
    stop_log_cleanup_task,
)
from src.users.api.routes import users_router

logger = AsyncSQLLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_token_cleanup_task() # Start the 24-hour cron job that deletes expired refresh tokens
    start_user_cleanup_task() # Start the 24-hour cron job that deletes unverified user accounts
    start_log_cleanup_task() # Start the cron job that cleans up old system logs from the DB
    start_log_worker_task() # Start the background queue worker that flushes active logs to the DB in batches
    yield
    # Gracefully shut down all background tasks before the app exits
    stop_token_cleanup_task()
    stop_user_cleanup_task()
    stop_log_cleanup_task()
    stop_log_worker_task()


openapi_tags = [
    {
        "name": "Auth",
        "description": "Core authentication flows including email/password registration, OAuth2 social logins, OTP email verification, secure session management, and password reset pipelines."
    },
    {
        "name": "Users",
        "description": "User profile management. Endpoints to fetch, update, and securely delete user accounts and their associated session data."
    }
]

app = FastAPI(
    title=app_settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs" if app_settings.ENV == "development" else None,
    redoc_url="/redoc" if app_settings.ENV == "development" else None,
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)

app.state.limiter = limiter
register_exception_handlers(app)

# In dev mode, we automatically whitelist common local frontend ports to save developers headaches
dev_origins = [
    "http://localhost:3000", "http://127.0.0.1:3000",   # Create React App / Next.js
    "http://localhost:5173", "http://127.0.0.1:5173",   # Vite (React/Vue/Svelte)
    "http://localhost:8000", "http://127.0.0.1:8000"    # FastAPI Swagger UI
]
origins = list(set(app_settings.cors_origins_list + (dev_origins if app_settings.ENV == "development" else [])))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF"]
)

app.add_middleware(
    SessionMiddleware,
    secret_key=app_settings.SESSION_SECRET,
    https_only=(app_settings.ENV != "development"),
    same_site="none" if app_settings.ENV != "development" else "lax",
)   

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(health_router)

if app_settings.ENV == "development":
    app.include_router(debug_email_router)

