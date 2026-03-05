# Legacy Core Banking API

This project is a Python REST API that exposes legacy banking data (CSV exports) through secure HTTP endpoints.

## Purpose

- Simulate integration of a legacy core banking data source with modern API consumers.
- Provide simple authentication, account/transaction APIs, and account status explanations.
- Offer a minimal web UI to test the API quickly.

## What is implemented

- FastAPI service with typed models.
- Token-based authentication (`/auth/token`, `/auth/logout`).
- Account endpoints:
	- `GET /accounts`
	- `GET /accounts/{account_id}`
	- `GET /accounts/{account_id}/transactions`
	- `GET /accounts/{account_id}/status-info`
- Status info table includes dormant/blocked explanations.
- `last_customer_activity_at` is computed dynamically from the latest transaction for the account.

## Run locally

```powershell
cd legacy-bank-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`
- UI: `http://127.0.0.1:8000/`

## Run with Docker

From project root:

```powershell
docker compose up --build
```

- Swagger: `http://127.0.0.1:8000/docs`
- UI: `http://127.0.0.1:8000/`

Stop the demo:

```powershell
docker compose down
```

Rebuild cleanly when needed:

```powershell
docker compose down --rmi local
docker compose up --build
```

## Authentication

- Login: `POST /auth/token` with JSON body:

```json
{"username":"ops","password":"ops-demo-2026"}
```

- Use returned bearer token in `Authorization: Bearer <token>`.
- Logout/revoke: `POST /auth/logout`.

## Scripts folder

`scripts/` contains helper tools for local development:

- `scripts/demo_requests.ps1`: runs a quick API demo flow.
- `scripts/manage_users.py`: create/list/activate/deactivate users in `data/users.json`.

User management examples:

```powershell
python scripts/manage_users.py list
python scripts/manage_users.py add --username engineer --password test-123 --role viewer
python scripts/manage_users.py deactivate --username engineer
python scripts/manage_users.py activate --username engineer
```

Default users:

- `ops / ops-demo-2026`
- `analyst / analyst-demo-2026`
