<div align="center">
  <h1>🛡️ FastAPI Modular Auth Template</h1>
  <p>A strictly typed, highly decoupled, enterprise-grade authentication foundation utilizing Hexagonal Architecture.</p>
</div>

---

## 📖 Introduction
This template provides a **strict, organized foundation** to handle authentication workflows. By utilizing Domain-Driven Design (DDD) and Hexagonal Architecture, the business logic remains pristine and uncoupled from infrastructure (FastAPI, SQLAlchemy, Redis). 

It is designed with security and enterprise-readiness in mind, featuring:
- **Strict Type Safety:** Enforcement of core domain models like `UUID` and `EmailStr` across all boundaries.
- **Advanced Session Management:** A dual-token architecture (HttpOnly Refresh Cookies + JWT Access Tokens) with lazy token rotation, session families, and remote device revocation.
- **Asynchronous Background Processing:** Built-in `TaskRunnerPort` for non-blocking operations like sending emails and writing system logs, easily swappable with Celery or RabbitMQ.

> **Infrastructure Independence:** Out of the box, this template is **SQL-based** (using SQLAlchemy & Alembic), but because the system is deeply modular, you are not locked in! You can easily swap out the SQL database, cache, or email provider by writing a new adapter. See [6. 🛠️ How to Change Core Infrastructure](#6-️-how-to-change-core-infrastructure) to learn how.

You can safely drop this into your new projects and focus immediately on building your core features, knowing the foundation is secure and highly decoupled.

> [!TIP]
> **React Frontend Companion**  
> We have built an official reference implementation demonstrating how to securely consume this API (handling stateless JWTs, silent token rotation, and CSRF protection). Check it out here: [Avneesh11905/Vite_React_OAuth_Frontend](https://github.com/Avneesh11905/Vite_React_OAuth_Frontend)

---

## 📑 Table of Contents
- [📖 Introduction](#-introduction)
- [📑 Table of Contents](#-table-of-contents)
- [1. 🏗️ Architecture Overview](#1-️-architecture-overview)
  - [1.1 The Domains](#11-the-domains)
  - [1.2 Inside Each Domain (Hexagonal Layers)](#12-inside-each-domain-hexagonal-layers)
  - [1.3 Transaction Management (Unit of Work)](#13-transaction-management-unit-of-work)
- [2. 🚀 Getting Started](#2--getting-started)
  - [2.1 Prerequisites](#21-prerequisites)
  - [2.2 Setup Instructions](#22-setup-instructions)
- [3. ⚙️ Environment Variables Guide](#3-️-environment-variables-guide)
  - [3.1 General \& Security](#31-general--security)
  - [3.2 Infrastructure](#32-infrastructure)
  - [3.3 Email Provider](#33-email-provider)
  - [3.4 OAuth Providers (Optional)](#34-oauth-providers-optional)
  - [3.5 Token, Verification \& Rate Limiting Thresholds](#35-token-verification--rate-limiting-thresholds)
- [4. 🔄 Authentication Workflows](#4--authentication-workflows)
  - [4.1 Local Registration](#41-local-registration)
  - [4.2 Login \& Session Issuance (Local)](#42-login--session-issuance-local)
  - [4.3 Login \& Session Issuance (OAuth)](#43-login--session-issuance-oauth)
  - [4.4 Session Rotation](#44-session-rotation)
  - [4.5 Logout \& Session Revocation](#45-logout--session-revocation)
- [5. 💻 Frontend Integration Guidelines](#5--frontend-integration-guidelines)
  - [5.1 📍 Required Frontend Routes](#51--required-frontend-routes)
  - [5.2 🗺️ API Reference Checklist](#52-️-api-reference-checklist)
    - [5.2.1 🔐 Authentication (`/auth` prefix)](#521--authentication-auth-prefix)
    - [5.2.2 👤 User Profile (`/users` prefix)](#522--user-profile-users-prefix)
  - [5.3 ♻️ Handling Token Rotation (Axios Example)](#53-️-handling-token-rotation-axios-example)
  - [5.4 🛡️ CSRF Protection Details](#54-️-csrf-protection-details)
- [6. 🛠️ How to Change Core Infrastructure](#6-️-how-to-change-core-infrastructure)
  - [6.1 Swapping the Cache (e.g., Redis -\> Memcached)](#61-swapping-the-cache-eg-redis---memcached)
  - [6.2 Swapping the Email Provider (e.g., Resend -\> SendGrid)](#62-swapping-the-email-provider-eg-resend---sendgrid)
  - [6.3 How to Change the Database (SQL -\> MongoDB)](#63-how-to-change-the-database-sql---mongodb)
  - [6.4 Adding Shared Infra (e.g. RabbitMQ, Celery)](#64-adding-shared-infra-eg-rabbitmq-celery)
  - [6.5 The Universal Swap Pattern (Any Adapter)](#65-the-universal-swap-pattern-any-adapter)
- [7. 🌍 Adding an OAuth Provider](#7--adding-an-oauth-provider)
  - [7.1 Adding a New Provider](#71-adding-a-new-provider)
  - [7.2 Removing a Provider](#72-removing-a-provider)
- [8. 🔐 Integrating Authorization](#8--integrating-authorization)
  - [8.1 How it Works (The Hexagonal Wiring)](#81-how-it-works-the-hexagonal-wiring)
  - [8.2 Defining Your Rules](#82-defining-your-rules)
  - [8.3 Protecting Routes](#83-protecting-routes)
- [9. 📧 Email Templates \& Developer Previews](#9--email-templates--developer-previews)
  - [9.1 🎨 The Dev Theme Gallery](#91--the-dev-theme-gallery)
- [10. ⚙️ Background Task Processing](#10-️-background-task-processing)
- [11. 🧪 Testing](#11--testing)
- [12. 🚨 Production Deployment Checklist](#12--production-deployment-checklist)
  - [12.1 Enforce Remote Caching](#121-enforce-remote-caching)
  - [12.2 Set Environment to Production (`ENV="production"`)](#122-set-environment-to-production-envproduction)
  - [12.3 Strictly Define CORS Origins](#123-strictly-define-cors-origins)
  - [12.4 Understand Cookie Boundaries (`SameSite`)](#124-understand-cookie-boundaries-samesite)
  - [12.5 Swap the Background Task Runner](#125-swap-the-background-task-runner)

---



## 1. 🏗️ Architecture Overview

The project is structured into modular domains using Domain-Driven Design (DDD) and Hexagonal Architecture. This ensures business logic remains pristine and uncoupled from infrastructure (FastAPI, SQLAlchemy, Redis).

### 1.1 The Domains
1. **`src/shared/`**: The backbone of the application. It contains infrastructure that spans across all domains, such as database connections (`get_db`), caching clients, the email configuration pipeline, application lifecycle events, and global exception handlers.
2. **`src/authentication/`**: Handles identity verification. It manages local registration, OAuth integrations, password resets, email verification, and issues JWTs. 
3. **`src/users/`**: Manages the user profile lifecycle (fetching profiles, updating display names, deleting accounts) independently from the authentication logic.
4. **`src/authorization/`**: Contains the business rules for access control (RBAC/PBAC) and injects permissions into your JWTs.

### 1.2 Inside Each Domain (Hexagonal Layers)
Each domain (except `shared`) is divided into distinct, decoupled layers:
- **Core (`core/`)**: Contains pure Python business rules and Use Cases. It has zero knowledge of FastAPI, SQLAlchemy, or external APIs.
- **Ports (`core/ports/`)**: Abstract interfaces (`typing.Protocol`) that define external dependencies required by the Core (e.g., `CachePort`, `EmailSenderPort`).
- **Adapters (`adapters/`)**: Concrete implementations of the Ports (e.g., `RedisCacheAdapter`, `SQLUserRepositoryAdapter`).
- **API (`api/`)**: FastAPI routes acting as the entry point. They translate HTTP requests into Python objects, execute Use Cases, and return HTTP responses.

> [!TIP]
> **Dependency Injection:** A centralized Composition Root (`api/container.py` inside each domain) instantiates all Adapters. This is bridged with FastAPI's native DI system using `typing.Annotated`, allowing routes to depend cleanly on use cases.

### 1.3 Transaction Management (Unit of Work)
This project enforces the **Unit of Work (UoW)** pattern to manage database transactions cleanly:
- Routes inject the `SQLAlchemyUnitOfWork` and wrap use case execution in an `async with uow:` block.
- Repositories **never** call `commit()` directly; they only perform data manipulation and `flush()`.
- The UoW automatically commits the transaction at the end of the block if successful, or rolls back if an exception occurs, ensuring atomicity across multiple repository operations.

---

## 2. 🚀 Getting Started

> **Note on Architecture:** Because this template strictly follows Clean Architecture, the default tech stack (PostgreSQL, Redis, Resend) is completely decoupled from the core logic and is **100% swappable**. You can easily replace the database, cache, or email provider by writing a new adapter. See [6. 🛠️ How to Change Core Infrastructure](#6-️-how-to-change-core-infrastructure) for a guide.

### 2.1 Prerequisites
- **Python 3.12+**
- **Database**: PostgreSQL (for production) or SQLite (built-in fallback for local development).
- **Cache**: Redis (recommended for production) or Memory (built-in fallback for local development).

### 2.2 Setup Instructions

**Option A: Using Docker (Recommended)**
1. Copy the configuration:
   ```bash
   cp .env.example .env
   ```
2. **Generate Security Keys (RS256)**:
   ```bash
   uv run python scripts/generate_keys.py
   ```
   *Copy the output and paste it into your `.env` file for `JWT_PRIVATE_KEY` and `JWT_PUBLIC_KEY`.*
3. Spin up the entire stack (API, PostgreSQL, Redis) with a single command:
   ```bash
   docker compose up --build
   ```

**Option B: Local Python Setup (Using uv)**
1. Ensure you have [`uv`](https://docs.astral.sh/uv/) installed.
2. Clone the repository and install dependencies:
   ```bash
   uv sync
   # Or, if using requirements.txt: uv venv && uv pip install -r requirements.txt
   ```
2. Copy the configuration:
   ```bash
   cp .env.example .env
   ```
3. **Generate Security Keys (RS256)**:
   ```bash
   uv run python scripts/generate_keys.py
   ```
4. **Choose your Cache**: The system defaults to `MemoryCacheAdapter` for local dev (which will log a warning). To use Redis, update `src/shared/container.py` to instantiate `RedisCacheAdapter(client=redis_client)`.
5. Run database migrations:
   ```bash
   uv run alembic upgrade head
   ```
6. Start the server:
   ```bash
   uv run python runserver.py
   ```

---

## 3. ⚙️ Environment Variables Guide

The `.env` file controls the entire behavior of the application without needing to touch code. Here is what every variable does:

### 3.1 General & Security
| Variable | Example | Description |
|---|---|---|
| `FRONTEND_URL` | `"http://localhost:3000"` | Used to build deep links (like password reset URLs) sent in emails. |
| `PROJECT_NAME` | `"FastAPI OAuth"` | The title shown in Swagger UI and the sender name in some emails. |
| `ENV` | `"development"` | <b>When `"development"`:</b> Enables development routes (like the email gallery), Swagger UI, and automatically adds local URLs (`http://localhost:3000`, `5173`, `8000`) to the allowed CORS origins.<br><br><b>When `"production"`:</b> Disables these development features and enforces strict cross-origin policies. |
| `CORS_ORIGINS` | `"https://myapp.com"` | Comma-separated list of allowed frontend URLs. Crucial for security. *(Note: If `ENV="development"`, `http://localhost:3000`, `5173`, and `8000` are automatically whitelisted, so you do not need to add them here).* |
| `SESSION_SECRET` | `"super_secret_string"` | Used to cryptographically sign the `X-CSRF` state validation. |
| `JWT_PRIVATE_KEY` | `"-----BEGIN RSA PRIVATE KEY-----..."` | Used to cryptographically *sign* the Access Tokens. |
| `JWT_PUBLIC_KEY` | `"-----BEGIN PUBLIC KEY-----..."` | Used to *verify* the Access Tokens. |

### 3.2 Infrastructure
| Variable | Example | Description |
|---|---|---|

| `LOG_RETENTION_DAYS` | `28` | How many days of system logs to keep in the database before the background worker deletes them. |
| `DB_ASYNC_URL` | `postgresql+asyncpg://...` | Connection string to your database. **Optional.** If omitted, falls back to a local SQLite database (`sqlite+aiosqlite:///./auth.db`). |
| `CACHE_URL` | `"redis://localhost:6379/0"` | Connection string to your Cache & Rate Limiting server. **Optional.** Defaults to `redis://localhost:6379/0`. Can be safely swapped to `memcached://...` without breaking the system. |

### 3.3 Email Provider
| Variable | Example | Description |
|---|---|---|
| `EMAIL_API_KEY` | `"re_123456789"` | Your Resend API key. |
| `EMAIL_FROM` | `"onboarding@resend.dev"` | The email address shown to users. Must be verified with your provider. |
| `EMAIL_TEMPLATE_NAME` | `"modern"` | Select the visual theme for all outbound emails (`modern`, `minimal`, `playful`). |

### 3.4 OAuth Providers (Optional)
| Variable | Example | Description |
|---|---|---|
| `GOOGLE_CLIENT_ID` | `"1234.apps.googleusercontent.com"` | From the Google Cloud Console. |
| `GOOGLE_CLIENT_SECRET` | `"GOCSPX-1234"` | From the Google Cloud Console. |
| `GITHUB_CLIENT_ID` | `"Iv1.1234"` | From GitHub Developer Settings. |
| `GITHUB_CLIENT_SECRET` | `"abc1234"` | From GitHub Developer Settings. |

### 3.5 Token, Verification & Rate Limiting Thresholds
| Variable | Example | Description |
|---|---|---|
| `TOKEN_ACCESS_TOKEN_LIFETIME_MINUTES` | `15` | How long the stateless JWT is valid. |
| `TOKEN_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | How long a user stays logged in before being forced to re-authenticate. |
| `VERIFICATION_OTP_EXPIRATION_SECONDS` | `300` | How long a 6-digit OTP is valid after being issued. |
| `VERIFICATION_OTP_RESEND_WINDOW_SECONDS` | `900` | The window within which OTP resend is allowed (keeps the pending registration alive). |
| `VERIFICATION_OTP_MAX_ATTEMPTS` | `5` | Maximum number of wrong OTP attempts before the flow is locked out and a new OTP must be requested. |
| `VERIFICATION_PASSWORD_RESET_EXPIRY_SECONDS` | `900` | How long a password reset token is valid after being issued. |
| `RATE_LIMIT_LOGIN_RATE_LIMIT` | `"5/minute"` | Strict slow-down on the login endpoints to prevent brute forcing. |
| `RATE_LIMIT_DEFAULT_RATE_LIMIT` | `"60/minute"` | Default API limit. |

> [!NOTE]
> **Prefix change:** OTP and password-reset settings previously used the `TOKEN_` prefix. They were moved to a dedicated `VerificationSettings` class and now use the `VERIFICATION_` prefix.

---

## 4. 🔄 Authentication Workflows

### 4.1 Local Registration
A database-first registration flow prevents malicious actors from claiming emails they don't own. 

- **The Flow:** A user is saved immediately with `is_verified=False`. If they do not verify their email using the 6-digit OTP within 5 minutes, the OTP expires. 
- **Retry Logic:** If the user abandons the flow and tries to register again hours later, the backend gracefully accepts it, updates their pending password, and dispatches a fresh OTP.
- **Brute-Force Protection:** The OTP flow implements atomic counting and strictly locks the account registration process after 5 failed attempts (requiring a new OTP request).
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

### 4.2 Login & Session Issuance (Local)
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

### 4.3 Login & Session Issuance (OAuth)
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

### 4.4 Session Rotation
To mitigate token theft, the system implements **lazy Refresh Token rotation**. Rather than rotating the token on every single call (which causes unnecessary DB writes), the token is only rotated when it has **≤ 30% of its lifetime remaining**. Most `/refresh` calls simply re-validate the existing token and issue a new Access Token without touching the Refresh Token at all.

```mermaid
sequenceDiagram
    participant Frontend
    participant AuthAPI as Auth Service
    participant Database
    
    Frontend->>AuthAPI: POST /auth/refresh (Cookie)
    AuthAPI->>Database: Validate Token (check used=False, not expired)
    alt Token lifetime > 30% remaining
        AuthAPI-->>Frontend: Set-Cookie: same refresh_token (no rotation)
    else Token lifetime ≤ 30% remaining
        AuthAPI->>Database: Mark old token used=True
        AuthAPI->>Database: Generate & Save NEW Refresh Token
        AuthAPI-->>Frontend: Set-Cookie: new_refresh_token
    end
    AuthAPI-->>Frontend: JSON: new_access_token (JWT)
```

### 4.5 Logout & Session Revocation
Logout and device revocation use two complementary mechanisms:

- **Access Token (`jti`) blacklist** — Because JWTs are stateless, the current access token's unique ID (`jti`) is written to the cache with a TTL equal to its remaining lifetime. Any subsequent request bearing that token is rejected immediately, even before it expires naturally.
- **Refresh Token soft-invalidation** — On logout, device revocation (`DELETE /auth/sessions/{family_id}`), **password changes**, or **password resets**, all refresh tokens in the session family are marked `used=True` in the database. No Redis `blacklist:family:*` key is written. Active access tokens from revoked sessions expire naturally within `ACCESS_TOKEN_LIFETIME_MINUTES` (default 15 min).

> [!NOTE]
> **Multi-worker note:** The per-`jti` blacklist still requires a shared cache (Redis) in multi-worker deployments. The family revocation check is DB-only and works correctly across workers without Redis.

---

## 5. 💻 Frontend Integration Guidelines

Building the frontend should be the fun part! Here is exactly what you need to wire up to get this authentication system humming.

### 5.1 📍 Required Frontend Routes
You only *have* to build two routes on your frontend to handle the core flows:

- 🏠 **`/` (The Root Route)**: Make sure your root route can handle post-login redirects and email verification success states.
- 🔑 **`/reset-password`**: This is where users land when they click the "Reset Password" link in their email.
  - **The Inbound Catch:** The user arrives via `GET /reset-password?token=YOUR_SECURE_TOKEN`. Your frontend needs to parse that `token` right out of the URL.
  - **The Outbound Pitch:** Show them a nice form asking for a new password. When they hit submit, shoot a `POST` request back to our backend at `/auth/password/reset` with this exact JSON payload: `{"token": "YOUR_SECURE_TOKEN", "new_password": "the_new_password"}`.

> [!IMPORTANT]
> **Token Mechanics:** The backend returns the **Access Token** in the JSON body, which you must attach as `Authorization: Bearer <token>` to protected API requests. The **Refresh Token** is set as a secure, `HttpOnly` cookie—so the browser handles it completely automatically!

> [!WARNING]
> **Account Deletion — 30-day Recovery Window:** `DELETE /users/me` performs a **soft-delete** — the account is immediately deactivated (the user cannot log in) and is scheduled for permanent purge after **30 days**. Within that window, the user can recover their account simply by logging in again. When the user logs in to recover their account, a security notification email is automatically dispatched. After 30 days, the account and all associated data (OAuth links, passwords, sessions) are permanently removed by a background cleanup task. Ensure your frontend clearly communicates this recovery window before calling this endpoint.

---

### 5.2 🗺️ API Reference Checklist

> [!TIP]
> **Interactive Documentation:** Run the backend and visit **`http://localhost:8000/docs`** for the auto-generated Swagger UI, or **`http://localhost:8000/redoc`** for ReDoc. You can test endpoints and see exactly what the JSON responses look like!

Here is your treasure map to the backend API. 

#### 5.2.1 🔐 Authentication (`/auth` prefix)
| Method | Endpoint | Description |
|:---:|---|---|
| `POST` | `/auth/register` | Creates a new user (`is_verified=False`) and dispatches a 6-digit OTP email. |
| `POST` | `/auth/verify-email` | Validates the OTP, unlocks the account, and **auto-logs the user in** — sets `refresh_token` + `csrf_token` cookies on success. The frontend should immediately call `POST /auth/refresh` to obtain the Access Token. |
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

#### 5.2.2 👤 User Profile (`/users` prefix)
| Method | Endpoint | Description |
|:---:|---|---|
| `GET` | `/users/me` | Fetches the currently authenticated user's profile data. **Note:** This endpoint implements Lazy Caching via Redis/Memory, resulting in zero database hits for successive calls. Cache is automatically invalidated upon updates. |
| `PATCH` | `/users/me` | Updates display name, profile picture, or the `receive_updates` opt-in preference. *(Requires `X-CSRF` header)*. |
| `DELETE`| `/users/me` | **Soft-deletes** the user's account. The account is immediately deactivated and scheduled for permanent purge after 30 days. Recoverable within that window by logging in again. Also blacklists the current JWT and clears the session cookie. *(Requires `X-CSRF` header)*. |

---

### 5.3 ♻️ Handling Token Rotation (Axios Example)
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

### 5.4 🛡️ CSRF Protection Details
To prevent Cross-Site Request Forgery (CSRF), state-changing operations on sensitive endpoints (like `PATCH /users/me` or `DELETE /users/me`) require an `X-CSRF` header.

**How it works:**
1. When a user authenticates, the backend automatically sets a secure, `HttpOnly` session cookie (the Refresh Token), and *also* sets a standard `csrf_token` cookie.
2. Because the `csrf_token` cookie is **not** `HttpOnly`, your frontend JavaScript (or Axios) can read it using `document.cookie`.
3. When making a state-changing request, your frontend must extract this token from the cookie and attach it as the `X-CSRF` header.
4. The backend verifies that the header matches the internal state, confirming the request originated from your actual frontend and not a malicious third-party site.

---

## 6. 🛠️ How to Change Core Infrastructure

One of the greatest strengths of this template is its plug-and-play nature. Because the Core business logic only communicates through **Ports**, you can completely replace any infrastructure by simply writing a new **Adapter**.

### 6.1 Swapping the Cache (e.g., Redis -> Memcached)
The template ships with two built-in cache adapters in the `shared` kernel: `MemoryCacheAdapter` and `RedisCacheAdapter`. To switch between them, open `src/shared/container.py` and instantiate the one you want.
To plug in a completely different backend (e.g., Memcached), follow the universal 3-step pattern in [6.5](#65-the-universal-swap-pattern-any-adapter) using the shared `CachePort` as your interface.

> [!TIP]
> **Automatic Rate Limiter Sync**  
> The built-in rate limiter (`slowapi`) automatically connects to whatever you specify in `CACHE_URL`. If you swap to Memcached, simply set `CACHE_URL="memcached://localhost:11211"` and both your custom Cache Adapter and the Rate Limiter will seamlessly switch over!

### 6.2 Swapping the Email Provider (e.g., Resend -> SendGrid)
To drastically simplify Developer Experience, email provider logic lives in the `shared` kernel. 
Currently, the template uses `ResendEmailClient`. To swap it:
1. Create a new file: `src/shared/adapters/sendgrid_email_client.py`.
2. Implement the `SharedEmailClientPort` protocol:
   ```python
   from src.shared.core.ports.email_client import SharedEmailClientPort

   class SendGridEmailClient:
       def send_email(self, to: str, subject: str, html: str) -> None:
           # SendGrid dispatch logic here (sync — called via run_in_executor)
           pass
   ```
3. Update the Composition Root in `src/authentication/api/container.py` to use your new adapter:
   ```python
   # Old: from src.shared.adapters.resend_email_client import ResendEmailClient
   # Old: email_client = ResendEmailClient(...)
   
   from src.shared.adapters.sendgrid_email_client import SendGridEmailClient
   email_client = SendGridEmailClient()
   ```
*Done! You don't have to touch Jinja2 templates or the authentication domain's business logic. All auth emails will seamlessly start using SendGrid.*

### 6.3 How to Change the Database (SQL -> MongoDB)
Because all database queries are abstracted behind Repository Ports, replacing PostgreSQL with MongoDB is straightforward:
1. Change `DB_ASYNC_URL` in your `.env` to your MongoDB connection string.
2. Edit `src/shared/config/database.py` and `src/shared/api/dependencies.py` to yield a MongoDB async client instead of an SQLAlchemy `AsyncSession`.
3. Create a new adapter `src/authentication/adapters/mongo_user_repository.py` that implements `UserRepositoryPort`.
4. Plug it into `src/authentication/api/container.py`.

### 6.4 Adding Shared Infra (e.g. RabbitMQ, Celery)
Want to use RabbitMQ instead of the built-in `AsyncioTaskRunner`?
1. **Define the Port**: The interface is already defined at `src/shared/core/ports/task_runner.py`.
2. **Create the Adapter**: Create `src/shared/adapters/rabbitmq_task_runner.py` that implements the `TaskRunnerPort`.
3. **Plug it in**: Open `container.py` and swap `AsyncioTaskRunner()` with `RabbitMQTaskRunner()`. Every domain will instantly start sending background tasks to your RabbitMQ queue.

### 6.5 The Universal Swap Pattern (Any Adapter)

The examples above follow the exact same 3-step recipe that applies to **every** adapter in this system. You are never locked in anywhere — if it has a Port, it can be swapped.

**The 3-step recipe:**
1. **Find the Port** — Locate the `typing.Protocol` interface in `src/<domain>/core/ports/` that defines the contract.
2. **Write a new Adapter** — Create a new file in `src/<domain>/adapters/` and implement every method the Port requires.
3. **Plug it in** — Open `src/<domain>/api/container.py` and swap out the old adapter instantiation for your new one. Nothing else needs to change.

> [!TIP]
> The Core business logic has **zero knowledge** of which adapter is plugged in. Swapping is purely a wiring concern confined to `container.py` — your use cases, routes, and tests don't need to be touched.

Here is every swappable port in the system:

| Port Interface | Located In | What It Controls |
|---|---|---|
| `SharedEmailClientPort` | `src/shared/core/ports/` | Email delivery provider (Resend, SendGrid, SMTP, etc.) |
| `CachePort` | `src/shared/core/ports/` | Caching backend (Redis, Memcached, in-memory, etc.) |
| `TaskRunnerPort` | `src/shared/core/ports/` | Background task engine (asyncio, Celery, RabbitMQ, etc.) |
| `EmailSenderPort` | `src/authentication/core/ports/` | Domain-specific auth email rendering logic |
| `AccessTokenPort` | `src/authentication/core/ports/security/` | JWT signing scheme (RS256, HS256, custom, etc.) |
| `UserRepositoryPort` | `src/authentication/core/ports/repository/` | User storage backend (PostgreSQL, MongoDB, etc.) |
| `ClaimsProviderPort` | `src/authentication/core/ports/` | Custom JWT claims / authorization rules |

---

## 7. 🌍 Adding an OAuth Provider

This template uses a dynamic **OAuth Registry** powered by Authlib. To add a new provider (e.g., Spotify, Discord), you simply create a single file. You do **not** need to touch any central configuration files or routing logic!

### 7.1 Adding a New Provider

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

*Done! The dynamic routes `/auth/login/discord` and `/auth/callback/discord` will automatically start working.*

> [!NOTE]
> **Zero boilerplate required.** The `oauth/__init__.py` uses `pkgutil` to **auto-discover** every module inside the `providers/` package at startup. You do **not** need to manually add an import to any `__init__.py` — simply creating the file is enough.

### 7.2 Removing a Provider

Because the system is fully modular, removing an unwanted provider is incredibly clean:
1. Delete the provider's file (e.g., `src/authentication/infrastructure/oauth/providers/google.py`).
2. (Optional) Remove the credentials from your `.env` file.

*The dynamic routes `/auth/login/google` and `/auth/callback/google` will instantly vanish from your API without leaving any dead code behind.*

---

## 8. 🔐 Integrating Authorization

This template natively handles **Authentication** (identity verification) but leaves **Authorization** (access control) open so you can implement Role-Based Access Control (RBAC) or Policy-Based Access Control (PBAC).

### 8.1 How it Works (The Hexagonal Wiring)
Because this template uses strict Clean Architecture, domains do not talk to each other directly. Instead, they communicate through Interfaces (Ports).
1. The **Authentication** domain needs to know what roles to inject into a user's JWT when they log in. It defines an interface called `ClaimsProviderPort`.
2. The **Authorization** domain contains your actual business rules for access control.
3. We bridge them using a single concrete class: `CustomAuthorizationAdapter` (located in `src/authorization/adapters/custom_authorization.py`). 
4. In the Dependency Injection container (`src/authentication/api/container.py`), we instantiate this adapter as `custom_claims_provider` and inject it into the Authentication system.

### 8.2 Defining Your Rules
To implement your custom RBAC/PBAC rules, edit the `CustomAuthorizationAdapter`:

```python
# src/authorization/adapters/custom_authorization.py
from uuid import UUID

class CustomAuthorizationAdapter(AuthorizationPort[AsyncSession]):
    
    # 1. Stateless Roles (Injected into JWT)
    async def get_custom_claims(self, session: AsyncSession, user_id: UUID) -> dict:
        # Example: Fetch user roles from the database
        roles = await self._fetch_user_roles(session, user_id)
        # These roles are embedded into the Access Token when the user logs in!
        return {"roles": roles} 

    # 2. Stateful Permissions (Live Database Check)
    async def has_permission(self, session: AsyncSession, user_id: UUID, action: str, resource: str) -> bool:
        # Example: Check if the user owns a specific document
        return await self._check_db_for_ownership(session, user_id, action, resource)
```

### 8.3 Protecting Routes
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

## 9. 📧 Email Templates & Developer Previews

This template uses beautifully styled Jinja2 HTML templates for all outbound emails (verification codes, password resets, welcome emails, etc.). These templates are located in `src/shared/templates/emails/`.

### 9.1 🎨 The Dev Theme Gallery
Building HTML emails is notoriously frustrating because you normally have to send an actual email to see what it looks like. We fixed that!

If `ENV="development"` is set in your `.env`, we expose a special suite of developer routes that render the email templates directly in your browser. 

Simply spin up the backend and navigate to the gallery root:
**`http://localhost:8000/dev/email/preview`**

Here you can:
- Browse and preview **all** templates side-by-side.
- Toggle between aesthetic themes (`Modern`, `Minimal`, `Playful`).
- Test responsiveness with `Desktop`, `Tablet`, and `Mobile` width constraints.
- Toggle `Dark Mode` to see how email clients (like Gmail) will invert your colors.

*(Note: These `/dev/` routes are strictly disabled when `ENV="production"`).*

---

## 10. ⚙️ Background Task Processing
FastAPI is incredibly fast, but sending emails or writing logs can block the event loop if executed synchronously. This template uses a background task pipeline to ensure APIs return instantly.

The `src/shared/adapters/task_runner/asyncio_task_runner.py` executes tasks in the background natively. You can queue a task anywhere in your code without needing a heavy Celery worker:

```python
from uuid import UUID
from src.shared.container import shared_container

async def my_slow_function(user_id: UUID) -> None:
    pass

# Push it to the background and return immediately
shared_container.task_runner.add_task(my_slow_function, user.id)
```

> [!WARNING]
> **Production Scaling:** The built-in `asyncio_task_runner` is incredibly convenient for lightweight tasks, but it stores pending tasks in RAM. If the server crashes, pending tasks are lost. For high-throughput or mission-critical enterprise applications, it is highly recommended to swap this out for a robust message queue/worker architecture. We provide a `CeleryTaskRunner` out of the box. Open `src/shared/container.py` and swap it in for production!

---

## 11. 🧪 Testing
The template is highly decoupled, making unit and integration testing incredibly easy. Tests are located in the `tests/` directory and use `pytest`.

To run the entire test suite:
```bash
uv run pytest tests/
```

- **Core Tests**: Located in `tests/core/`. These test the pure business logic without spinning up a database or HTTP server.
- **API Tests**: Located in `tests/api/`. These spin up an ephemeral SQLite database to test the FastAPI routes end-to-end.

---

## 12. 🚨 Production Deployment Checklist

Before deploying this template to a live environment, you **must** verify the following:

### 12.1 Enforce Remote Caching
The default `MemoryCacheAdapter` uses a built-in Python dictionary. In a multi-worker production environment (e.g., `gunicorn -w 4`), **each worker will have an isolated cache**. This completely breaks **Rate Limiting** and **per-`jti` Access Token blacklisting** (used on logout). Note that session family revocation is DB-based and works correctly across workers without Redis. Open `src/shared/container.py` and swap to `RedisCacheAdapter` before deploying.

> [!WARNING]
> The `asyncio.Lock` inside `MemoryCacheAdapter` provides no cross-process protection. It only guards against concurrent access within a single worker process.

### 12.2 Set Environment to Production (`ENV="production"`)
Leaving `ENV="development"` in production exposes the `/dev/email/preview` gallery routes to the public and disables secure cookie validation.

### 12.3 Strictly Define CORS Origins
Ensure `CORS_ORIGINS` is explicitly defined in your `.env` (e.g., `CORS_ORIGINS="https://myapp.com,https://admin.myapp.com"`). Never leave it as a wildcard `*` in production, as this opens the API up to Cross-Origin attacks.

### 12.4 Understand Cookie Boundaries (`SameSite`)
Because the system relies on an `HttpOnly` cookie for the Refresh Token, the frontend and backend must either share a domain (e.g., `api.example.com` and `app.example.com`) or you must strictly configure your Reverse Proxy/Load Balancer to handle CORS and `SameSite=None; Secure` cookie attributes properly. Otherwise, the browser will silently block the refresh token cookie.

### 12.5 Swap the Background Task Runner
As noted above, the built-in `asyncio_task_runner` holds pending tasks in RAM. If the server crashes, pending emails or logs are lost. Swap this out for a robust message queue (Celery/Kafka) if you require guaranteed task execution.
