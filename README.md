# Finance Tracking System Backend
![alt text](image.png)
A FastAPI backend for managing financial transactions with role-based access control and analytics.

## Tech Stack

- FastAPI
- SQLAlchemy
- SQLite (default)
- JWT authentication (`python-jose`)
- Password hashing (`passlib` + `pbkdf2_sha256`)
- Pytest for tests
- Alembic for migrations

## Features

- User registration and login
- Access token + refresh token auth flow
- Role-based access (`viewer`, `analyst`, `admin`)
- Transaction CRUD
- Transaction filtering, search, pagination, and sorting
- CSV import/export for transactions
- Analytics summary (income, expenses, balance, category and monthly totals)
- Input validation and clear error responses

## Role Matrix

- `viewer`
  - Can view their own transactions
- `analyst`
  - Can view their own transactions
  - Can access analytics summary
- `admin`
  - Can create, update, delete transactions
  - Can view all transactions
  - Can access analytics summary

## Setup

1. Create and activate virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create env file:

```powershell
Copy-Item .env.example .env
```

4. Apply database migrations:

```powershell
alembic upgrade head
```

5. Run server:

```powershell
uvicorn app.main:app --reload
```

6. Open API docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Environment Variables

See `.env.example`:

- `DATABASE_URL`
- `SECRET_KEY`
- `TOKEN_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DEFAULT_PAGE_SIZE`
- `MAX_PAGE_SIZE`

## API Summary

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

### Transactions

- `POST /transactions/` (admin)
- `GET /transactions/` (authenticated, role-aware visibility)
- `GET /transactions/export` (authenticated, CSV download)
- `POST /transactions/import` (admin, CSV upload)
- `GET /transactions/{id}` (authenticated, ownership enforced for non-admin)
- `PUT /transactions/{id}` (admin)
- `DELETE /transactions/{id}` (admin)

`GET /transactions/` supports:

- `type`
- `category`
- `categories` (comma-separated)
- `search` (category/notes)
- `amount_min`, `amount_max`
- `from_date`, `to_date`
- `skip`, `limit`
- `sort_by` (`id`, `date`, `amount`, `category`, `type`)
- `sort_order` (`asc`, `desc`)

### Analytics

- `GET /analytics/summary` (analyst/admin)

## Testing

Run all tests:

```powershell
pytest -v
```

Run with coverage (optional):

```powershell
pytest --cov=app --cov-report=term-missing
```

## Database Migrations

Alembic is configured for schema migrations.

Create a migration after model changes:

```powershell
alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```powershell
alembic upgrade head
```

If you already have a local SQLite database created by the app startup code, align Alembic with the existing schema first:

```powershell
alembic stamp head
```

Rollback one migration:

```powershell
alembic downgrade -1
```

## Assumptions

- Admin has global visibility and write access.
- Viewer and analyst are read-only for transactions and restricted to their own records.
- Analytics is available only to analyst/admin.
- SQLite is used by default for local simplicity.

## Usage Steps
Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) and follow this order.

1. Register users first
- Expand `POST /auth/register`
- Create one `viewer`, one `analyst`, and one `admin`
- Keep the credentials simple so you can reuse them in later requests

2. Log in each user
- Expand `POST /auth/login`
- Use the username/password form
- Copy the `access_token` from the response
- In Swagger, click `Authorize` and paste `Bearer <token>`

3. Test transaction creation
- Use the admin token
- Call `POST /transactions/`
- Try a normal payload like:
```json
{
  "amount": 1500,
  "type": "income",
  "category": "salary",
  "notes": "monthly pay"
}
```
- Confirm admin can create successfully
- Then try the same as viewer/analyst and confirm it is blocked

4. Test transaction listing and filtering
- Use `GET /transactions/`
- As viewer or analyst, confirm you only see your own records
- Try filters one by one:
- `type=income`
- `category=salary`
- `search=pay`
- `amount_min=100`
- `amount_max=2000`
- `skip=0&limit=5`
- `sort_by=date&sort_order=desc`

5. Test single-record ownership
- Use `GET /transactions/{id}`
- As a different non-admin user, try to open someone else’s transaction
- Confirm you get `403`
- As admin, confirm you can view any transaction

6. Test update and delete
- Use the admin token
- Call `PUT /transactions/{id}` with a small change
- Call `DELETE /transactions/{id}`
- Confirm the record is updated or removed

7. Test analytics
- Use the analyst token
- Call `GET /analytics/summary`
- Confirm you get totals, category breakdown, monthly totals, and recent activity
- Try with viewer token and confirm it is blocked

8. Test token refresh and logout
- Use `POST /auth/login`
- Save both access and refresh tokens
- Call `POST /auth/refresh` with the refresh token
- Call `POST /auth/logout` with the access token
- Try the old access token again and confirm it is rejected

9. Test CSV import/export
- Use admin token
- Call `GET /transactions/export` and confirm a CSV download
- Call `POST /transactions/import` with a CSV file like:
```csv
amount,type,category,date,notes
100,income,salary,2026-01-01T10:00:00,bonus
25,expense,food,2026-01-02T12:00:00,lunch
```
- Confirm it imports and shows up in `GET /transactions/`

10. Run automated tests
- From the project root, run:
```powershell
pytest -q
```
- You should see all tests pass



## **Project Tour**

At a high level, the app is split into five layers: app startup, database/config, auth, business rules, and route handlers. The main entry point is main.py, which wires in the routers and exposes the root endpoint. The data models live in models.py, the request/response contracts in schemas.py, and the shared auth/database helpers in auth.py, dependencies.py, database.py, and config.py.

The backend flow is:
1. User registers or logs in through auth.py.
2. Auth helpers create and verify tokens in auth.py.
3. Dependency guards in dependencies.py enforce whether the request is from a valid user, analyst, or admin.
4. Transaction CRUD and filters are handled in transactions.py.
5. Analytics summary is generated in analytics.py.

**What each part does**

- models.py: Defines the database tables for users and transactions, including roles, ownership, timestamps, and the transaction type enum.
- schemas.py: Validates incoming payloads and shapes outgoing responses. This is where the amount/date/category rules live.
- auth.py: Hashes passwords, creates JWTs, refreshes tokens, and handles token revocation.
- dependencies.py: Figures out the current user from the bearer token and blocks unauthorized access.
- auth.py: Register, login, refresh, and logout endpoints.
- transactions.py: Create, list, export, import, update, delete, and single-record access for transactions.
- analytics.py: Returns the finance summary.
- database.py: Creates the SQLAlchemy engine/session and reads the database URL from env settings.
- config.py: Loads environment variables and provides the app settings.
- alembic/: Database migration setup.
- tests/: Automated coverage for auth, transactions, analytics, and optional endpoints.

**How it fits together in practice**

If you log in, the app returns tokens from auth.py. Those tokens are checked by dependencies.py whenever you hit protected routes. If you create a transaction, transactions.py uses schemas.py to validate the payload, models.py to save it, and database.py to talk to SQLite or another configured database. Analytics reads the same transaction data and aggregates it in analytics.py.