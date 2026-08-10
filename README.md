# Inventory Management API

A FastAPI backend for managing inventory items and users, with JWT-based authentication and role-based access control (RBAC). Built on SQLAlchemy + Alembic + PostgreSQL, with Docker Compose support for local development.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Option A: Docker Compose](#option-a-docker-compose-recommended)
  - [Option B: Local (native Python + Postgres)](#option-b-local-native-python--postgres)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Creating the First Admin User](#creating-the-first-admin-user)
- [Running Tests](#running-tests)
- [API Overview](#api-overview)
  - [Auth](#auth-authprefix)
  - [Users](#users-usersprefix)
  - [Admin](#admin-adminprefix)
  - [Items](#items-itemprefix)
- [Roles & Permissions](#roles--permissions)
- [Known Issues / Roadmap](#known-issues--roadmap)

## Features

- JWT-based authentication (OAuth2 password flow)
- Role-based access control: `admin`, `manager`, `viewer`
- User self-service (view profile, change password)
- Admin user management (list, view, change role, deactivate, delete, create)
- Item/inventory CRUD with filtering (category, price range, stock, search) and pagination
- Alembic-managed schema migrations
- Dockerized Postgres, backend, migrations, and admin bootstrap as separate Compose services

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Database | PostgreSQL (dev/prod). Tests currently run on **SQLite** — see [Known Issues](#known-issues--roadmap) |
| Auth | python-jose (JWT), passlib/bcrypt |
| Testing | pytest, FastAPI `TestClient` |
| Containerization | Docker, Docker Compose |

## Project Structure

```
.
├── app/
│   ├── main.py            # FastAPI app instance, router registration, CORS
│   ├── database.py        # Engine/session setup, reads DATABASE_URL
│   ├── env_utils.py        # get_required_env() — shared env accessor (avoids circular imports)
│   ├── models.py           # SQLAlchemy models: Users, Items
│   ├── schemas.py           # Pydantic request/response schemas + enums
│   ├── dependencies.py       # DB session, JWT decoding, get_current_user, require_role
│   └── routers/
│       ├── auth.py          # Registration + login/token
│       ├── users.py         # Self-service profile endpoints
│       ├── admin.py         # Admin-only user management
│       └── items.py         # Item CRUD
├── alembic/
│   ├── env.py
│   └── versions/
├── scripts/
│   └── create_admin.py      # Idempotent bootstrap script for the first admin user
├── test/
│   ├── conftest.py          # Test fixtures, DB override, auth override
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_admin.py
│   └── test_items.py
├── docker-compose.yml        # pgdb, backend, alembic, create-admin services
├── dockerfile
├── .env.example
├── .env.test                # Test environment config (Postgres-backed)
└── requirements.txt
```

## Getting Started

### Option A: Docker Compose (recommended)

**Prerequisites:** Docker and Docker Compose installed.

1. Copy the example environment file and fill in real values:

   ```bash
   cp .env.example .env
   ```

   Fill in `DB_USERNAME`, `DB_PASSWORD`, and `DB_NAME` — `DATABASE_URL` derives from these automatically via `${...}` interpolation, so you only need to set credentials in one place.

2. Bring the stack up:

   ```bash
   docker compose up --build
   ```

   This will, in order:
   - Start `pgdb` (Postgres) and wait for its healthcheck to pass
   - Run `alembic upgrade head` via the `alembic` service
   - Run `scripts/create_admin.py` via the `create-admin` service (only after migrations succeed)
   - Start the `backend` service on `http://localhost:8000`

3. Interactive API docs are available at `http://localhost:8000/docs`.

> **Note:** Inside Docker, services must talk to each other via the Compose service name (`pgdb`), not `localhost`. `DATABASE_URL` in `.env.example` already uses `pgdb` as the host for this reason.

### Option B: Local (native Python + Postgres)

**Prerequisites:** Python 3.11+, a running local PostgreSQL instance.

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a database and set up your `.env` (see [Environment Variables](#environment-variables)), using `localhost` for `DATABASE_URL` since there's no Compose network here.

3. Apply migrations:

   ```bash
   alembic upgrade head
   ```

4. Bootstrap the admin user:

   ```bash
   python -m scripts.create_admin
   ```

5. Run the server:

   ```bash
   uvicorn app.main:app --reload
   ```

## Environment Variables

Defined in `.env` (git-ignored) for the app, and `.env.test` for the test suite. See `.env.example`:

```dotenv
DB_USERNAME=your-database_username-here
DB_PASSWORD=your-database-password-here
DB_NAME=your-database-name-here
DATABASE_URL = "postgresql://${DB_USERNAME}:${DB_PASSWORD}@pgdb:5432/${DB_NAME}"
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ADMIN_USERNAME=your-username-here
ADMIN_EMAIL=your-email-here
ADMIN_PASSWORD=your-password-here
```

| Variable | Description |
|---|---|
| `DB_USERNAME` | Postgres username — used both to provision the `pgdb` container and inside `DATABASE_URL` |
| `DB_PASSWORD` | Postgres password — same dual purpose as above |
| `DB_NAME` | Postgres database name — same dual purpose as above |
| `DATABASE_URL` | SQLAlchemy connection string, built from `DB_USERNAME`/`DB_PASSWORD`/`DB_NAME` via `${...}` interpolation. `python-dotenv` resolves this, so `DB_USERNAME`/`DB_PASSWORD`/`DB_NAME` **must be defined above `DATABASE_URL` in the file** |
| `SECRET_KEY` | Secret used to sign JWTs |
| `ALGORITHM` | JWT signing algorithm (e.g. `HS256`) |
| `ADMIN_USERNAME` | Username for the bootstrap admin account |
| `ADMIN_EMAIL` | Email for the bootstrap admin account |
| `ADMIN_PASSWORD` | Password for the bootstrap admin account |

All required env vars are read through `app/env_utils.get_required_env`, which raises a clear `ValueError` if a variable is missing, rather than failing silently or falling back to `None`.

> **Host differs by environment:** `DATABASE_URL` above uses `pgdb` as the host, which is correct for Docker Compose (containers reach Postgres via the service name). For a native/local run with no Compose network (see [Option B](#option-b-local-native-python--postgres)), change the host to `localhost` in your own `.env`.


## Database Migrations

Migrations live in `alembic/versions/`. Common commands:

```bash
# Apply all pending migrations
alembic upgrade head

# Generate a new migration from model changes
alembic revision --autogenerate -m "describe your change"

# Roll back one revision
alembic downgrade -1
```

`alembic/env.py` reads `DATABASE_URL` via `get_required_env`, so it respects whatever `.env` is loaded in the current shell/container — no hardcoded connection string in `alembic.ini` is actually used at runtime.

## Creating the First Admin User

`scripts/create_admin.py` is idempotent: it only creates an admin if no user with `role == 'admin'` already exists, using `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` from the environment. Safe to run repeatedly (e.g. on every container start).

## Running Tests

Tests use `pytest`. `.env.test` is loaded in `test/conftest.py` before any app modules are imported, to avoid environment variable race conditions.

```bash
pytest -v
```

Test client and DB overrides:
- `get_db` is overridden to use a `TestingSessionLocal` session
- `get_current_user` is overridden to return a fixed identity, with role swappable per-test via the `as_role` fixture
- Fixtures (`test_user`, `test_viewer_user`, `test_item`, `test_items_multiple`) insert rows and clean them up via a raw `DELETE FROM` in teardown


## API Overview

Interactive, always-current documentation is available at `/docs` (Swagger UI) and `/redoc` once the server is running. Summary below.

### Auth (`/auth` prefix)

| Method | Path | Description | Auth required |
|---|---|---|---|
| POST | `/auth/` | Register a new user (always created as `viewer`) | No |
| POST | `/auth/token` | Log in (OAuth2 password flow), returns a JWT bearer token | No |

### Users (`/users` prefix)

| Method | Path | Description | Auth required |
|---|---|---|---|
| GET | `/users/` | Get the current authenticated user's profile | Yes |
| PUT | `/users/password` | Change the current user's password | Yes |

### Admin (`/admin` prefix)

All endpoints require the `admin` role.

| Method | Path | Description |
|---|---|---|
| GET | `/admin/users` | List all users |
| GET | `/admin/users/{user_id}` | Get a single user by ID |
| PUT | `/admin/users/{user_id}/role` | Change a user's role |
| PUT | `/admin/users/{user_id}/deactivate` | Deactivate a user (cannot deactivate self) |
| DELETE | `/admin/users/{user_id}` | Delete a user (cannot delete self) |
| POST | `/admin/create-user` | Create a new user with an arbitrary role |

### Items (`/item` prefix)

| Method | Path | Description | Auth required |
|---|---|---|---|
| GET | `/item/` | List items with optional filters: `category`, `min_price`, `max_price`, `in_stock_only`, `search`, plus `skip`/`limit` pagination | Yes (any role) |
| GET | `/item/{item_id}` | Get a single item | Yes (any role) |
| POST | `/item/` | Create an item | `admin` or `manager` |
| PUT | `/item/{item_id}` | Update an item | `admin` or `manager` |
| DELETE | `/item/{item_id}` | Delete an item | `admin` or `manager` |

## Roles & Permissions

| Role | Can view items | Can manage items | Can manage users |
|---|---|---|---|
| `viewer` | ✅ | ❌ | ❌ |
| `manager` | ✅ | ✅ | ❌ |
| `admin` | ✅ | ✅ | ✅ |

Role enforcement is handled by the `require_role(*roles)` dependency in `app/dependencies.py`, which checks the role embedded in the JWT payload against the requesting user's active session.
