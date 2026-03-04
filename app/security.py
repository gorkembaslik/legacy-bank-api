from datetime import datetime, timedelta, UTC
import json
from pathlib import Path
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

TOKEN_TTL_SECONDS = 1800
security_scheme = HTTPBearer(auto_error=False)
BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "data" / "users.json"

DEFAULT_USERS = [
    {
        "username": "ops",
        "password": "ops-demo-2026",
        "role": "admin",
        "active": True,
    },
    {
        "username": "analyst",
        "password": "analyst-demo-2026",
        "role": "viewer",
        "active": True,
    },
]

ACTIVE_TOKENS: dict[str, dict[str, datetime | str]] = {}


def _ensure_users_file() -> None:
    if USERS_FILE.exists():
        return
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(DEFAULT_USERS, indent=2), encoding="utf-8")


def _load_users() -> list[dict[str, str | bool]]:
    _ensure_users_file()
    raw = USERS_FILE.read_text(encoding="utf-8")
    return json.loads(raw)


def _save_users(users: list[dict[str, str | bool]]) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def list_users() -> list[dict[str, str | bool]]:
    users = _load_users()
    return [
        {
            "username": str(user["username"]),
            "role": str(user.get("role", "viewer")),
            "active": bool(user.get("active", False)),
        }
        for user in users
    ]


def upsert_user(username: str, password: str, role: str = "viewer", active: bool = True) -> None:
    users = _load_users()
    existing = next((u for u in users if u.get("username") == username), None)
    if existing:
        existing["password"] = password
        existing["role"] = role
        existing["active"] = active
    else:
        users.append(
            {
                "username": username,
                "password": password,
                "role": role,
                "active": active,
            }
        )
    _save_users(users)


def set_user_active(username: str, active: bool) -> bool:
    users = _load_users()
    for user in users:
        if user.get("username") == username:
            user["active"] = active
            _save_users(users)
            return True
    return False


def _get_user(username: str) -> dict[str, str | bool] | None:
    users = _load_users()
    return next((u for u in users if u.get("username") == username), None)


def authenticate_user(username: str, password: str) -> bool:
    user = _get_user(username)
    if not user:
        return False
    if not bool(user.get("active", False)):
        return False
    expected_password = str(user.get("password", ""))
    return secrets.compare_digest(password, expected_password)


def issue_token(username: str, ttl_seconds: int = TOKEN_TTL_SECONDS) -> tuple[str, int]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
    user = _get_user(username)
    role = str(user.get("role", "viewer")) if user else "viewer"
    ACTIVE_TOKENS[token] = {
        "username": username,
        "role": role,
        "expires_at": expires_at,
    }
    return token, ttl_seconds


def revoke_token(token: str) -> None:
    ACTIVE_TOKENS.pop(token, None)


def _is_token_valid(token: str) -> bool:
    payload = ACTIVE_TOKENS.get(token)
    if not payload:
        return False
    expires_at = payload["expires_at"]
    if not isinstance(expires_at, datetime):
        return False
    if datetime.now(UTC) >= expires_at:
        ACTIVE_TOKENS.pop(token, None)
        return False
    return True


def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized: missing bearer token")

    token = credentials.credentials
    if not _is_token_valid(token):
        raise HTTPException(status_code=401, detail="Unauthorized: invalid or expired token")

    return token
