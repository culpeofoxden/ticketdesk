# TicketDesk MVP

Zendesk-like ticket system MVP built with FastAPI, React, Tailwind, PostgreSQL, SQLAlchemy, Alembic, Pydantic, and JWT authentication.

## Quick Start

```bash
docker compose up --build
```

Services:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`

## Demo Users

The backend seeds these users at startup if they do not exist:

| Email | Password | Role |
| --- | --- | --- |
| admin@example.com | password | admin |
| agent@example.com | password | agent |
| customer@example.com | password | customer |

## Authentication

### Register

`POST /auth/register`

Request body:

```json
{
  "email": "new.customer@example.com",
  "password": "password",
  "role": "customer"
}
```

Allowed roles:

- `admin`
- `agent`
- `customer`

`email` must be unique. Passwords are stored only as bcrypt hashes.

The request also accepts optional `full_name`; if omitted, the backend derives it from the email prefix.

### Login

`POST /auth/login`

Request body:

```json
{
  "email": "admin@example.com",
  "password": "password"
}
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "full_name": "Admin User",
    "role": "admin",
    "created_at": "..."
  }
}
```

### Current User

`GET /auth/me`

Requires a bearer token and returns the authenticated user.

## Using JWT in Swagger

1. Open http://localhost:8000/docs.
2. Run `POST /auth/login` with one of the demo users.
3. Copy `access_token` from the response.
4. Click `Authorize` at the top of Swagger.
5. Paste only the token value into the HTTP Bearer field.
6. Run protected endpoints such as `GET /auth/me`.

## Alembic

Run migrations locally from the `backend` folder:

```bash
alembic upgrade head
```

Docker runs `alembic upgrade head` before starting Uvicorn.

## Local Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Project Structure

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
  migrations/
frontend/
docker-compose.yml
README.md
```

## Main Auth Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

