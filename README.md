<div align="center">
  <h1>🛡️ FastAPI Modular Auth Template</h1>
  <p>A strictly typed, highly decoupled, enterprise-grade authentication foundation utilizing Hexagonal Architecture.</p>
</div>

---

## 📖 Introduction
This template provides a **strict, organized foundation** to handle authentication workflows. By utilizing Domain-Driven Design (DDD) and Hexagonal Architecture, the business logic remains pristine and uncoupled from infrastructure (FastAPI, SQLAlchemy, Redis). 

You can safely drop this into your new projects, easily swap out infrastructure components (like the database, email provider, or cache), and focus immediately on building your core features.

> [!TIP]
> **React Frontend Companion**  
> We have built an official reference implementation demonstrating how to securely consume this API (handling stateless JWTs, silent token rotation, and CSRF protection). Check it out here: [Avneesh11905/Vite_React_OAuth_Frontend](https://github.com/Avneesh11905/Vite_React_OAuth_Frontend)

---

## 📑 Table of Contents
- [📖 Introduction](#-introduction)
- [🏗️ Architecture Overview](#️-architecture-overview)
  - [The Domains](#the-domains)
  - [Inside Each Domain (Hexagonal Layers)](#inside-each-domain-hexagonal-layers)
- [🛠️ How to Swap Adapters](#️-how-to-swap-adapters)
  - [1. Swapping the Email Provider (e.g., Resend -\> SendGrid)](#1-swapping-the-email-provider-eg-resend---sendgrid)
  - [2. Swapping the Cache (e.g., Redis -\> Memcached)](#2-swapping-the-cache-eg-redis---memcached)
  - [3. Swapping Security Tokens (e.g., RS256 -\> Custom Scheme)](#3-swapping-security-tokens-eg-rs256---custom-scheme)
- [🌍 Adding an OAuth Provider](#-adding-an-oauth-provider)
  - [Removing a Provider](#removing-a-provider)
- [🔐 Integrating Authorization](#-integrating-authorization)
  - [How it Works (The Hexagonal Wiring)](#how-it-works-the-hexagonal-wiring)
  - [1. Defining Your Rules](#1-defining-your-rules)
  - [2. Protecting Routes](#2-protecting-routes)
- [🚀 Getting Started](#-getting-started)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Setup Instructions](#2-setup-instructions)
- [⚙️ Environment Variables Guide](#️-environment-variables-guide)
  - [General Settings](#general-settings)
  - [Infrastructure](#infrastructure)
  - [Security Keys](#security-keys)
  - [Email Provider (Resend)](#email-provider-resend)
  - [OAuth Providers (Optional)](#oauth-providers-optional)
- [🔄 Authentication Workflows](#-authentication-workflows)
  - [1. Local Registration](#1-local-registration)
  - [2. Login \& Session Issuance](#2-login--session-issuance)
  - [3. Session Rotation](#3-session-rotation)
  - [4. Logout \& Blacklisting](#4-logout--blacklisting)
- [💻 Frontend Integration Guidelines](#-frontend-integration-guidelines)
  - [📍 1. Required Frontend Routes](#-1-required-frontend-routes)
  - [🗺️ 2. API Reference Checklist](#️-2-api-reference-checklist)
  - [♻️ 3. Handling Token Rotation (Axios Example)](#️-3-handling-token-rotation-axios-example)
  - [🛡️ 4. CSRF Protection Details](#️-4-csrf-protection-details)
- [📧 Email Templates & Developer Previews](#-email-templates--developer-previews)
  - [🎨 The Dev Theme Gallery](#-the-dev-theme-gallery)
- [⚙️ Background Task Processing](#️-background-task-processing)
- [🧪 Testing](#-testing)
- [🚨 Production Deployment Checklist](#-production-deployment-checklist)

---



## 🏗️ Architecture Overview

The project is structured into modular domains using Domain-Driven Design (DDD) and Hexagonal Architecture. This ensures business logic remains pristine and uncoupled from infrastructure (FastAPI, SQLAlchemy, Redis).

### The Domains
1. **`src/shared/`**: The backbone of the application. It contains infrastructure that spans across all domains, such as database connections (`get_db`), caching clients, the email configuration pipeline, application lifecycle events, and global exception handlers.
2. **`src/authentication/`**: Handles identity verification. It manages local registration, OAuth integrations, password resets, email verification, and issues JWTs. 
3. **`src/users/`**: Manages the user profile lifecycle (fetching profiles, updating display names, deleting accounts) independently from the authentication logic.
4. **`src/authorization/`**: Contains the business rules for access control (RBAC/PBAC) and injects permissions into your JWTs.

### Inside Each Domain (Hexagonal Layers)
Each domain (except `shared`) is divided into distinct, decoupled layers:
- **Core (`core/`)**: Contains pure Python business rules and Use Cases. It has zero knowledge of FastAPI, SQLAlchemy, or external APIs.
- **Ports (`core/ports/`)**: Abstract interfaces (`typing.Protocol`) that define external dependencies required by the Core (e.g., `CachePort`, `EmailSenderPort`).
- **Adapters (`adapters/`)**: Concrete implementations of the Ports (e.g., `RedisCacheAdapter`, `SQLUserRepositoryAdapter`).
- **API (`api/`)**: FastAPI routes acting as the entry point. They translate HTTP requests into Python objects, execute Use Cases, and return HTTP responses.

> [!TIP]
> **Dependency Injection:** A centralized Composition Root (`api/container.py` inside each domain) instantiates all Adapters. This is bridged with FastAPI's native DI system using `typing.Annotated`, allowing routes to depend cleanly on use cases.

---

## 🛠️ How to Swap Adapters

One of the greatest strengths of this template is its plug-and-play nature. Because the Core business logic only communicates through **Ports**, you can completely replace any infrastructure by simply writing a new **Adapter**.

### 1. Swapping the Email Provider (e.g., Resend -> SendGrid)
Currently, the template uses `ResendAdapter`. To swap it:
1. Create a new file: `src/authentication/adapters/email/sendgrid_adapter.py`.
2. Implement the `EmailSenderPort` protocol:
   ```python
   from src.authentication.core.ports import EmailSenderPort

   class SendGridAdapter(EmailSenderPort):
       async def send_verification_email(self, to_email: str, otp: str) -> None:
           # SendGrid logic here
           pass
           
       async def send_password_reset_email(self, to_email: str, reset_url: str) -> None:
           # SendGrid logic here
           pass
           
       async def send_welcome_email(self, to_email: str, name: str) -> None:
           # SendGrid logic here
           pass
   ```
3. Update the Composition Root in `src/authentication/api/container.py` to use your new adapter:
   ```python
   # Old: from src.authentication.adapters.email.email_sender import ResendAdapter
   # Old: email_sender = ResendAdapter(...)
   
   from src.authentication.adapters.email.sendgrid_adapter import SendGridAdapter
   email_sender = SendGridAdapter()
   ```
*Done! The core use cases will seamlessly start using SendGrid without any logic changes.*

### 2. Swapping the Cache (e.g., Redis -> Memcached)
1. Write a new adapter implementing `CachePort` in `src/authentication/adapters/cache/memcached_adapter.py`.
2. Swap the instantiation in `src/authentication/api/container.py`.

### 3. Swapping Security Tokens (e.g., RS256 -> Custom Scheme)
If you want to use a different token payload or signing mechanism:
1. Implement the `AccessTokenPort` (in `src/authentication/core/ports/security/access_token.py`).
2. Swap the dependency in `container.py`.

---

## 🌍 Adding an OAuth Provider

This template uses a dynamic **OAuth Registry** powered by Authlib. To add a new provider (e.g., Spotify, Discord), you simply create a single file. You do **not** need to touch any central configuration files or routing logic!

1. Add your provider's credentials to your `.env` file:
   ```env
   DISCORD_CLIENT_ID="your_client_id"
   DISCORD_CLIENT_SECRET="your_client_secret"
   ```

2. Create a new file in `src/authentication/infrastructure/oauth/providers/discord.py`.
3. Use the dynamic `oauth_settings` to grab your credentials, and the `@oauth_registry.register_provider` decorator to register the provider:

    ```python
    from src.authentication.infrastructure.oauth.registry import oauth_registry
    from src.authentication.core.domain.user import OAuthUserInfo
    from src.shared.config import oauth_settings

    # 1. Fetch credentials dynamically from the .env file!
    client_id, client_secret = oauth_settings.get_credentials("discord")

    @oauth_registry.register_provider(
        "discord",
        client_id=client_id,
        client_secret=client_secret,
        api_base_url="https://discord.com/api/",
        authorize_url="https://discord.com/api/oauth2/authorize",
        access_token_url="https://discord.com/api/oauth2/token",
        client_kwargs={"scope": "identify email"},
    )
    async def parse_discord_user(provider, token: dict) -> OAuthUserInfo:
        # 2. Fetch user data from the provider
        response = await provider.get("users/@me", token=token)
        data = response.json()
        
        # 3. Return a standardized profile for the Core domain
        return OAuthUserInfo(
            provider="discord",
            sub=str(data["id"]),
            email=data.get("email"),
            name=data.get("username"),
            picture=None 
        )
    ```

4. Import your new file inside `src/authentication/infrastructure/oauth/__init__.py` to ensure the decorator runs when the app boots:
    ```python
    import src.authentication.infrastructure.oauth.providers.discord
    ```

*Done! The dynamic routes `/auth/login/discord` and `/auth/callback/discord` will automatically start working.*

### Removing a Provider

Because the system is fully modular, removing an unwanted provider is incredibly clean:
1. Delete the provider's file (e.g., `src/authentication/infrastructure/oauth/providers/google.py`).
2. Remove the `import` statement from `src/authentication/infrastructure/oauth/__init__.py`.
3. (Optional) Remove the credentials from your `.env` file.

*The dynamic routes `/auth/login/google` and `/auth/callback/google` will instantly vanish from your API without leaving any dead code behind.*

---

## 🔐 Integrating Authorization

This template natively handles **Authentication** (identity verification) but leaves **Authorization** (access control) open so you can implement Role-Based Access Control (RBAC) or Policy-Based Access Control (PBAC).

### How it Works (The Hexagonal Wiring)
Because this template uses strict Clean Architecture, domains do not talk to each other directly. Instead, they communicate through Interfaces (Ports).
1. The **Authentication** domain needs to know what roles to inject into a user's JWT when they log in. It defines an interface called `ClaimsProviderPort`.
2. The **Authorization** domain contains your actual business rules for access control.
3. We bridge them using a single concrete class: `CustomAuthorizationAdapter` (located in `src/authorization/adapters/custom_authorization.py`). 
4. In the Dependency Injection container (`src/authentication/api/container.py`), we instantiate this adapter as `custom_claims_provider` and inject it into the Authentication system.

### 1. Defining Your Rules
To implement your custom RBAC/PBAC rules, edit the `CustomAuthorizationAdapter`:

```python
# src/authorization/adapters/custom_authorization.py
class CustomAuthorizationAdapter(AuthorizationPort[AsyncSession]):
    
    # 1. Stateless Roles (Injected into JWT)
    async def get_custom_claims(self, session: AsyncSession, user_id: str) -> dict:
        # Example: Fetch user roles from the database
        roles = await self._fetch_user_roles(session, user_id)
        # These roles are embedded into the Access Token when the user logs in!
        return {"roles": roles} 

    # 2. Stateful Permissions (Live Database Check)
    async def has_permission(self, session: AsyncSession, user_id: str, action: str, resource: str) -> bool:
        # Example: Check if the user owns a specific document
        return await self._check_db_for_ownership(session, user_id, action, resource)
```

### 2. Protecting Routes
Now that your rules are defined in the adapter, you can enforce them on any FastAPI route using the built-in dependencies:

```python
from fastapi import APIRouter, Depends
from src.authorization.api.dependencies import require_role, require_permission

router = APIRouter()

# Stateless check: Fast, no DB hit. 
# It reads the "roles" array from the JWT (populated by get_custom_claims).
@router.post("/admin/dashboard", dependencies=[Depends(require_role("admin"))])
async def view_dashboard():
    pass

# Stateful check: Granular, queries the DB.
# This triggers the has_permission() method in your CustomAuthorizationAdapter.
@router.delete("/documents/{id}", dependencies=[Depends(require_permission("delete", "document"))])
async def delete_document(id: str):
    pass
```

---

## 🚀 Getting Started

> **Note on Architecture:** Because this template strictly follows Clean Architecture, the default tech stack (PostgreSQL, Redis, Resend) is completely decoupled from the core logic and is **100% swappable**. You can easily replace the database, cache, or email provider by writing a new adapter. See [🛠️ How to Swap Adapters](#️-how-to-swap-adapters) for a guide.

### 1. Prerequisites
- **Python 3.11+**
- **PostgreSQL**: Persistent storage for Users and Refresh Tokens.
- **Cache**: Redis (recommended for production) or Memory (built-in, for local development).

### 2. Setup Instructions

**Option A: Using Docker (Recommended)**
1. Copy the configuration:
   ```bash
   cp .env.example .env
   ```
2. **Generate Security Keys (RS256)**:
   ```bash
   python scripts/generate_keys.py
   ```
   *Copy the output and paste it into your `.env` file for `JWT_PRIVATE_KEY` and `JWT_PUBLIC_KEY`.*
3. Spin up the entire stack (API, PostgreSQL, Redis) with a single command:
   ```bash
   docker compose up --build
   ```

**Option B: Local Python Setup**
1. Clone the repository and install dependencies:
   ```bash
   python -m venv venv
   # Windows: .\venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy the configuration:
   ```bash
   cp .env.example .env
   ```
3. **Generate Security Keys (RS256)**:
   ```bash
   python scripts/generate_keys.py
   ```
4. Set the `CACHE_TYPE` in `.env`:
   - `CACHE_TYPE="redis"`: Requires a local Redis server running.
   - `CACHE_TYPE="memory"`: Uses a thread-safe Python dictionary.
5. Run database migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the server:
   ```bash
   python runserver.py
   ```

---

## ⚙️ Environment Variables Guide

The `.env` file controls the entire behavior of the application without needing to touch code. Here is what every variable does:

### General & Security
| Variable | Example | Description |
|---|---|---|
| `FRONTEND_URL` | `"http://localhost:3000"` | Used to build deep links (like password reset URLs) sent in emails. |
| `PROJECT_NAME` | `"FastAPI OAuth"` | The title shown in Swagger UI and the sender name in some emails. |
| `DEV` | `True` or `False` | Enables development routes (like the email gallery), auto-reloading, and Swagger UI. Must be `False` in production. |
| `CORS_ORIGINS` | `"https://myapp.com"` | Comma-separated list of allowed frontend URLs. Crucial for security. *(Note: If `DEV=True`, `http://localhost:3000`, `5173`, and `8000` are automatically whitelisted, so you do not need to add them here).* |
| `SESSION_SECRET` | `"super_secret_string"` | Used to cryptographically sign the `X-CSRF` state validation. |
| `JWT_PRIVATE_KEY` | `"-----BEGIN RSA PRIVATE KEY-----..."` | Used to cryptographically *sign* the Access Tokens. |
| `JWT_PUBLIC_KEY` | `"-----BEGIN PUBLIC KEY-----..."` | Used to *verify* the Access Tokens. |

### Infrastructure
| Variable | Example | Description |
|---|---|---|
| `CACHE_TYPE` | `"redis"` or `"memory"` | Determines the caching backend. MUST be `"redis"` in production for rate limits and JWT blacklists. |
| `LOG_RETENTION_DAYS` | `28` | How many days of system logs to keep in the database before the background worker deletes them. |
| `DB_ASYNC_URL` | `postgresql+asyncpg://...` | Connection string to your PostgreSQL database. |
| `REDIS_HOST` | `"auth_redis"` | Hostname or IP for your Redis server. |
| `REDIS_PORT` | `6379` | Port for your Redis server. |
| `REDIS_DB` | `0` | Redis logical database index. |
| `REDIS_USERNAME` | `""` | Optional. Used for managed providers like Upstash or Redis Enterprise. |
| `REDIS_PASSWORD` | `"secure_pass"` | Optional. Used for managed providers or secured self-hosted Redis. |

### Email Provider
| Variable | Example | Description |
|---|---|---|
| `EMAIL_API_KEY` | `"re_123456789"` | Your Resend API key. |
| `EMAIL_FROM` | `"onboarding@resend.dev"` | The email address shown to users. Must be verified with your provider. |
| `EMAIL_TEMPLATE_NAME` | `"modern"` | Select the visual theme for all outbound emails (`modern`, `minimal`, `playful`). |

### OAuth Providers (Optional)
| Variable | Example | Description |
|---|---|---|
| `GOOGLE_CLIENT_ID` | `"1234.apps.googleusercontent.com"` | From the Google Cloud Console. |
| `GOOGLE_CLIENT_SECRET` | `"GOCSPX-1234"` | From the Google Cloud Console. |
| `GITHUB_CLIENT_ID` | `"Iv1.1234"` | From GitHub Developer Settings. |
| `GITHUB_CLIENT_SECRET` | `"abc1234"` | From GitHub Developer Settings. |

### Token & Rate Limiting Thresholds
| Variable | Example | Description |
|---|---|---|
| `TOKEN_ACCESS_TOKEN_LIFETIME_MINUTES` | `15` | How long the stateless JWT is valid. |
| `TOKEN_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | How long a user stays logged in before being forced to re-authenticate. |
| `RATE_LIMIT_LOGIN_RATE_LIMIT` | `"5/minute"` | Strict slow-down on the login endpoints to prevent brute forcing. |
| `RATE_LIMIT_DEFAULT_RATE_LIMIT` | `"60/minute"` | Default API limit. |

---

## 🔄 Authentication Workflows

### 1. Local Registration
A database-first registration flow prevents malicious actors from claiming emails they don't own. 

- **The Flow:** A user is saved immediately with `is_verified=False`. If they do not verify their email using the 6-digit OTP within 15 minutes, the OTP expires. 
- **Retry Logic:** If the user abandons the flow and tries to register again hours later, the backend gracefully accepts it, updates their pending password, and dispatches a fresh OTP.
- **Garbage Collection:** To prevent database bloat from bots, a background task automatically purges unverified user accounts older than 24 hours.

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant AuthAPI as Auth Service
    participant Database
    participant Email
    
    User->>Frontend: Submits Email & Password
    Frontend->>AuthAPI: POST /auth/register
    AuthAPI->>Database: Save User (is_verified=False)
    AuthAPI->>Email: Dispatch 6-digit OTP
    AuthAPI-->>Frontend: 201 Created
    
    User->>Frontend: Submits OTP
    Frontend->>AuthAPI: POST /auth/verify-email
    AuthAPI->>Database: Mark is_verified=True
    AuthAPI-->>Frontend: 200 OK
```

### 2. Login & Session Issuance (Local)
A dual-token system is utilized for security:
- **Refresh Token**: 32-byte hash saved in the DB, sent to the client as an `HttpOnly` Secure cookie.
- **Access Token**: Short-lived (15m) RS256 JWT returned in the JSON payload from the `/refresh` endpoint.

To keep the frontend logic DRY, the `/login` endpoints use a "Silent Auth" pattern where they only issue the Refresh Cookie, forcing the frontend to immediately call `/refresh` to get the access token.

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant AuthAPI as Auth Service
    participant Database
    
    User->>Frontend: Enters Credentials
    Frontend->>AuthAPI: POST /auth/login/local
    AuthAPI->>Database: Validate Hash & is_verified
    AuthAPI->>Database: Generate & Save Refresh Token
    AuthAPI-->>Frontend: Set-Cookie: refresh_token (HttpOnly)
    
    Note over Frontend,AuthAPI: Frontend automatically fetches access token
    Frontend->>AuthAPI: POST /auth/refresh (Cookie)
    AuthAPI->>Database: Rotate Refresh Token
    AuthAPI-->>Frontend: Set-Cookie: new_refresh_token
    AuthAPI-->>Frontend: JSON: access_token (JWT)
```

### 3. Login & Session Issuance (OAuth)
The OAuth flow relies on redirects. Once the provider confirms identity, the backend sets the HttpOnly cookie and redirects the browser back to the frontend. The frontend then calls `/refresh` on boot.

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant AuthAPI as Auth Service
    participant Provider as Google/GitHub
    
    User->>Frontend: Clicks "Login with Google"
    Frontend->>AuthAPI: GET /auth/login/google
    AuthAPI-->>User: 302 Redirect to Provider
    User->>Provider: Grants permission
    Provider-->>AuthAPI: 302 Redirect back to /callback/google?code=...
    AuthAPI->>Provider: Exchanges code for Profile
    AuthAPI->>Database: Create/Update User & Generate Refresh Token
    AuthAPI-->>Frontend: 302 Redirect to Frontend URL + Set-Cookie: refresh_token (HttpOnly)
    
    Note over Frontend,AuthAPI: Frontend automatically fetches access token on boot
    Frontend->>AuthAPI: POST /auth/refresh (Cookie)
    AuthAPI-->>Frontend: JSON: access_token (JWT)
```

### 3. Session Rotation
To mitigate token theft, the Refresh Token is rotated on every use at the `/refresh` endpoint. The old token is invalidated, and a new one is issued.

```mermaid
sequenceDiagram
    participant Frontend
    participant AuthAPI as Auth Service
    participant Database
    
    Frontend->>AuthAPI: POST /auth/refresh (Cookie)
    AuthAPI->>Database: Validate & Invalidate Old Token
    AuthAPI->>Database: Generate & Save NEW Refresh Token
    AuthAPI-->>Frontend: Set-Cookie: new_refresh_token
    AuthAPI-->>Frontend: JSON: new_access_token (JWT)
```

### 4. Logout & Blacklisting
Because Access Tokens (JWTs) are stateless, they cannot be deleted from the database. On logout, the token's unique ID (`jti`) is added to a Cache Blacklist until it naturally expires.

---

## 💻 Frontend Integration Guidelines

Building the frontend should be the fun part! Here is exactly what you need to wire up to get this authentication system humming.

### 📍 1. Required Frontend Routes
You only *have* to build two routes on your frontend to handle the core flows:

- 🏠 **`/` (The Root Route)**: Make sure your root route can handle post-login redirects and email verification success states.
- 🔑 **`/reset-password`**: This is where users land when they click the "Reset Password" link in their email.
  - **The Inbound Catch:** The user arrives via `GET /reset-password?token=YOUR_SECURE_TOKEN`. Your frontend needs to parse that `token` right out of the URL.
  - **The Outbound Pitch:** Show them a nice form asking for a new password. When they hit submit, shoot a `POST` request back to our backend at `/auth/password/reset` with this exact JSON payload: `{"token": "YOUR_SECURE_TOKEN", "new_password": "the_new_password"}`.

> [!IMPORTANT]
> **Token Mechanics:** The backend returns the **Access Token** in the JSON body, which you must attach as `Authorization: Bearer <token>` to protected API requests. The **Refresh Token** is set as a secure, `HttpOnly` cookie—so the browser handles it completely automatically!

---

### 🗺️ 2. API Reference Checklist

> [!TIP]
> **Interactive Documentation:** Run the backend and visit **`http://localhost:8000/docs`** for the auto-generated Swagger UI, or **`http://localhost:8000/redoc`** for ReDoc. You can test endpoints and see exactly what the JSON responses look like!

Here is your treasure map to the backend API. 

#### 🔐 Authentication (`/auth` prefix)
| Method | Endpoint | Description |
|:---:|---|---|
| `POST` | `/auth/register` | Creates a new user (`is_verified=False`) and dispatches a 6-digit OTP email. |
| `POST` | `/auth/verify-email` | Validates the OTP and unlocks the account. |
| `POST` | `/auth/verify-email/resend` | Lost the code? Generates and emails a brand new OTP. |
| `POST` | `/auth/login/local` | Authenticates with email/password. Boom! You've got an `HttpOnly` session cookie! (Call `/auth/refresh` for the JWT). |
| `GET` | `/auth/login/{provider}` | Redirects the user to an OAuth provider (e.g., `/auth/login/google`). |
| `GET` | `/auth/callback/{provider}` | Handles the OAuth provider redirect and establishes the session. |
| `POST` | `/auth/refresh` | Rotates the `HttpOnly` Refresh Token cookie and issues a fresh JWT. |
| `POST` | `/auth/password/forgot`| Starts the "Forgot Password" flow. Emails a link with a short-lived reset token. |
| `POST` | `/auth/password/reset`| Completes the "Forgot Password" flow. Accepts the token and a new password. |
| `PATCH` | `/auth/password`| Updates the authenticated user's password. *(Requires `X-CSRF` header)* |
| `POST` | `/auth/logout` | Blacklists the current JWT and destroys the session cookies. |
| `GET` | `/auth/sessions` | Lists all active device sessions for the user, including the `auth_provider` (e.g. `local`, `google`). Perfect for a "Security" settings page. |
| `DELETE`| `/auth/sessions/{family_id}` | Revokes a specific remote session, instantly logging that device out. |

#### 👤 User Profile (`/users` prefix)
| Method | Endpoint | Description |
|:---:|---|---|
| `GET` | `/users/me` | Fetches the currently authenticated user's profile data (ID, email, name, picture, receive_updates, and `login_methods`). |
| `PATCH` | `/users/me` | Updates display name, profile picture, or the `receive_updates` opt-in preference. *(Requires `X-CSRF` header)*. |
| `DELETE`| `/users/me` | Permanently wipes the account and cascades deletion to all linked data. *(Requires `X-CSRF` header)*. |

---

### ♻️ 3. Handling Token Rotation (Axios Example)
Nobody likes being randomly logged out. Use an HTTP interceptor to automatically catch `401 Unauthorized` responses, silently call the `/auth/refresh` endpoint to get a new Access Token, and retry their pending request transparently!

> [!TIP]
> **Pro-tip:** Here's a copy-paste ready Axios interceptor to handle token rotation seamlessly.

```javascript
axios.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        // If it's a 401 and we haven't already retried this exact request...
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                // Silently request a new token using the HttpOnly Refresh Token cookie!
                const { data } = await axios.post('/auth/refresh');
                
                // Update headers and retry the original request
                axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
                originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
                return axios(originalRequest);
                
            } catch (refreshError) {
                // If the refresh fails, their session is dead. Boot them to login.
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);
```

---

### 🛡️ 4. CSRF Protection Details
To prevent Cross-Site Request Forgery (CSRF), state-changing operations on sensitive endpoints (like `PATCH /users/me` or `DELETE /users/me`) require an `X-CSRF` header.

**How it works:**
1. When a user authenticates, the backend automatically sets a secure, `HttpOnly` session cookie (the Refresh Token), and *also* sets a standard `csrf_token` cookie.
2. Because the `csrf_token` cookie is **not** `HttpOnly`, your frontend JavaScript (or Axios) can read it using `document.cookie`.
3. When making a state-changing request, your frontend must extract this token from the cookie and attach it as the `X-CSRF` header.
4. The backend verifies that the header matches the internal state, confirming the request originated from your actual frontend and not a malicious third-party site.

---

## 📧 Email Templates & Developer Previews

This template uses beautifully styled Jinja2 HTML templates for all outbound emails (verification codes, password resets, welcome emails, etc.). These templates are located in `src/shared/templates/emails/`.

### 🎨 The Dev Theme Gallery
Building HTML emails is notoriously frustrating because you normally have to send an actual email to see what it looks like. We fixed that!

If `DEV=True` is set in your `.env`, we expose a special suite of developer routes that render the email templates directly in your browser. 

Simply spin up the backend and navigate to the gallery root:
**`http://localhost:8000/dev/email/preview`**

Here you can:
- Browse and preview **all** templates side-by-side.
- Toggle between aesthetic themes (`Modern`, `Minimal`, `Playful`).
- Test responsiveness with `Desktop`, `Tablet`, and `Mobile` width constraints.
- Toggle `Dark Mode` to see how email clients (like Gmail) will invert your colors.

*(Note: These `/dev/` routes are strictly disabled when `DEV=False` in production).*

---

## ⚙️ Background Task Processing
FastAPI is incredibly fast, but sending emails or writing logs can block the event loop if executed synchronously. This template uses a background task pipeline to ensure APIs return instantly.

The `src/shared/infrastructure/asyncio_task_runner.py` executes tasks in the background natively. You can queue a task anywhere in your code without needing a heavy Celery worker:

```python
from src.authentication.api.container import get_container

async def my_slow_function(user_id: str):
    pass

# Push it to the background and return immediately
get_container().task_runner.add_task(my_slow_function, user.id)
```

> [!WARNING]
> **Production Scaling:** The built-in `asyncio_task_runner` is incredibly convenient for lightweight tasks, but it stores pending tasks in RAM. If the server crashes, pending tasks are lost. For high-throughput or mission-critical enterprise applications, it is highly recommended to swap this out for a robust message queue/worker architecture like **Celery**, **Kafka**, or **RabbitMQ**. Because the system uses a `TaskRunnerPort` interface, you can easily plug in a Celery Adapter without altering your use cases!

---

## 🧪 Testing
The template is highly decoupled, making unit and integration testing incredibly easy. Tests are located in the `tests/` directory and use `pytest`.

To run the entire test suite:
```bash
pytest tests/
```

- **Core Tests**: Located in `tests/core/`. These test the pure business logic without spinning up a database or HTTP server.
- **API Tests**: Located in `tests/api/`. These spin up an ephemeral SQLite database to test the FastAPI routes end-to-end.

---

## 🚨 Production Deployment Checklist

Before deploying this template to a live environment, you **must** verify the following:

### 1. Enforce Redis Caching (`CACHE_TYPE="redis"`)
If you leave `CACHE_TYPE="memory"` in your `.env`, the app uses a built-in Python dictionary. In a multi-worker production environment (e.g., `gunicorn -w 4`), **each worker will have an isolated cache**. This completely breaks Rate Limiting and JWT Blacklisting. **Production MUST use Redis.**

### 2. Disable Developer Mode (`DEV=False`)
Leaving `DEV=True` in production exposes the `/dev/email/preview` gallery routes to the public and may trigger `uvicorn` to run in `--reload` mode, which consumes massive amounts of CPU and memory.

### 3. Strictly Define CORS Origins
Ensure `CORS_ORIGINS` is explicitly defined in your `.env` (e.g., `CORS_ORIGINS="https://myapp.com,https://admin.myapp.com"`). Never leave it as a wildcard `*` in production, as this opens the API up to Cross-Origin attacks.

### 4. Understand Cookie Boundaries (`SameSite`)
Because the system relies on an `HttpOnly` cookie for the Refresh Token, the frontend and backend must either share a domain (e.g., `api.example.com` and `app.example.com`) or you must strictly configure your Reverse Proxy/Load Balancer to handle CORS and `SameSite=None; Secure` cookie attributes properly. Otherwise, the browser will silently block the refresh token cookie.

### 5. Swap the Background Task Runner
As noted above, the built-in `asyncio_task_runner` holds pending tasks in RAM. If the server crashes, pending emails or logs are lost. Swap this out for a robust message queue (Celery/Kafka) if you require guaranteed task execution.
