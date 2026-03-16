# Secure Enterprise Auth System

[![CI](https://github.com/jgrillo18/secure-enterprise-auth-system/actions/workflows/ci.yml/badge.svg)](https://github.com/jgrillo18/secure-enterprise-auth-system/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange.svg)](https://github.com/astral-sh/ruff)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/jgrillo18/secure-enterprise-auth-system)

**🚀 Live demo:** https://secure-enterprise-auth-system.onrender.com

Enterprise-grade authentication system with JWT, refresh tokens, rate limiting and secure password hashing — designed for SaaS, microservices and cloud APIs.

---

## Features

| Feature | Implementation |
|---|---|
| JWT access tokens | `python-jose` · HS256 · 30-min expiry |
| Refresh tokens | Persisted in DB · 7-day expiry · rotation-safe |
| Password hashing | `passlib` · bcrypt · auto-salted |
| Rate limiting | `slowapi` · per-IP · configurable limits |
| CSRF protection | `secrets.token_hex` · constant-time comparison |
| Input validation | Pydantic v2 · email format · password strength rules |
| User enumeration prevention | Identical error response for bad email / bad password |
| Structured logging | Python `logging` · timestamped · log-level aware |
| Non-root Docker image | Dedicated `appuser` — no root privileges at runtime |
| PostgreSQL / SQLite | Switchable via `DATABASE_URL` env var |
| Web UI | Built-in dark-mode UI · EN/ES bilingual · live password rules |
| CI/CD | GitHub Actions · tests on Python 3.9 & 3.11 · Docker build check |

---

## Project Structure

```
secure-enterprise-auth-system/
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI pipeline
├── app/
│   ├── main.py               # FastAPI app factory, middleware, router
│   ├── models/
│   │   ├── base.py           # SQLAlchemy Base re-export
│   │   └── user.py           # User ORM model
│   ├── schemas/
│   │   └── auth_schema.py    # Pydantic request / response schemas
│   ├── routes/
│   │   └── auth_routes.py    # /auth endpoints with rate-limit decorators
│   ├── services/
│   │   └── auth_service.py   # Business logic (register, login, refresh)
│   ├── static/
│   │   └── index.html        # Built-in Web UI (dark mode, EN/ES)
│   └── utils/
│       ├── database.py       # Engine, session factory, get_db dependency
│       ├── security.py       # bcrypt + JWT helpers
│       ├── rate_limiter.py   # SlowAPI limiter instance
│       └── csrf.py           # CSRF token generation & validation
├── tests/
│   └── test_auth.py          # pytest integration tests (TestClient)
├── .env.example              # Environment variable template
├── .gitignore
├── docker-compose.yml        # App + PostgreSQL stack
├── Dockerfile                # Production image (non-root)
├── LICENSE
└── requirements.txt
```

---

## Quick Start

### Option 1 — Deploy to Render (online, gratis)

1. Haz clic en el botón **Deploy to Render** arriba  
2. Inicia sesión en [render.com](https://render.com) con tu cuenta de GitHub  
3. Render detectará el `render.yaml` y creará automáticamente:
   - **Web Service** — la API con FastAPI
   - **PostgreSQL database** — gratis incluida
4. Haz clic en **Apply** — en ~3 minutos estará en vivo

**Live demo:** https://secure-enterprise-auth-system.onrender.com  
**API docs:** https://secure-enterprise-auth-system.onrender.com/docs

---

### Option 2 — Docker Compose (PostgreSQL local)

```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
docker-compose up --build
```

### Option 3 — Local (SQLite)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # set SECRET_KEY
uvicorn app.main:app --reload
```

The API and Web UI will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## Web UI

A built-in dark-mode dashboard is served at `http://localhost:8000` with:

- **Register** — create an account with live password strength rules
- **Login** — get JWT access token, refresh token and CSRF token
- **Active Session** — view and copy tokens with one click
- **Refresh** — rotate the access token without logging in again
- **Health check** — ping the service status
- **EN / ES** — bilingual toggle button (English / Español)

---

## API Endpoints

### `POST /auth/register`
Create a new user account.

**Request body**
```json
{ "email": "user@example.com", "password": "SecurePass1" }
```

**Password rules:** ≥ 8 characters · at least 1 uppercase · at least 1 digit

**Response `201`**
```json
{ "message": "Account created successfully.", "user_id": 1 }
```

---

### `POST /auth/login`
Validate credentials and obtain token pair.

**Request body**
```json
{ "email": "user@example.com", "password": "SecurePass1" }
```

**Response `200`**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "csrf_token": "<hex>"
}
```

---

### `POST /auth/refresh`
Exchange a refresh token for a new access token.

**Request body**
```json
{ "refresh_token": "<jwt>" }
```

**Response `200`**
```json
{ "access_token": "<new_jwt>", "token_type": "bearer" }
```

---

### `GET /auth/health`
Liveness check — returns `200` when the service is running.

---

## Rate Limits

| Endpoint | Limit |
|---|---|
| `POST /auth/register` | 5 requests / minute / IP |
| `POST /auth/login` | 10 requests / minute / IP |
| `POST /auth/refresh` | 20 requests / minute / IP |

Exceeding a limit returns **`429 Too Many Requests`**.

---

## Running Tests

```bash
# Activate venv first
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

pytest tests/ -v
```

Tests use an isolated SQLite database — no external services required.  
The CI pipeline runs tests automatically on every push to `main`.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./auth.db` | SQLAlchemy connection string |
| `SECRET_KEY` | *(insecure default)* | JWT signing key — **must** be changed in production |
| `ACCESS_EXPIRE_MINUTES` | `30` | Access token lifetime in minutes |
| `REFRESH_EXPIRE_DAYS` | `7` | Refresh token lifetime in days |

Generate a strong secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Security Notes

- **SECRET_KEY** must never be committed to version control. Use `.env` (gitignored) or a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.).
- The Docker image runs as a non-root user (`appuser`) to reduce the blast radius of container escapes.
- Failed login attempts return the same `401` message regardless of whether the email exists, preventing user enumeration attacks.
- CSRF tokens use `secrets.compare_digest` for constant-time comparison — safe against timing attacks.
- For production deployments, restrict `allow_origins` in the CORS middleware to your actual frontend domain.

---

## Use Cases

- SaaS backends requiring secure multi-tenant authentication
- Microservice auth gateway (issue tokens here, verify them in downstream services)
- Cloud-native APIs that need to meet enterprise security baselines
- Starter template for teams that need JWT + refresh token flows from day one

---

## License

MIT — see [LICENSE](LICENSE) for details.
