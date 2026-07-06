from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API_TOKEN_FILE_NAME = "api_tokens.json"
TOKEN_STORE_VERSION = 1


class ApiTokenStoreError(RuntimeError):
    """Raised when the local API token registry cannot be read or written."""


def api_token_store_path(
    *,
    data_root: str | Path | None = None,
    path: str | Path | None = None,
) -> Path:
    if path is not None:
        return Path(path).expanduser().resolve()
    env_path = os.getenv("AXDATA_API_TOKEN_FILE")
    if env_path:
        return Path(env_path).expanduser().resolve()
    root = Path(data_root or os.getenv("AXDATA_DATA_DIR", "data")).expanduser().resolve()
    return root.parent / "metadata" / API_TOKEN_FILE_NAME


def api_auth_enabled(*, data_root: str | Path | None = None, api_host: str | None = None) -> bool:
    if os.getenv("AXDATA_API_TOKEN"):
        return True
    if os.getenv("AXDATA_API_AUTH_REQUIRED", "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    if is_loopback_host(api_host or os.getenv("AXDATA_API_HOST", "127.0.0.1")):
        return False
    path = api_token_store_path(data_root=data_root)
    if not path.exists():
        return False
    try:
        _read_store(path)
    except ApiTokenStoreError:
        return True
    return True


def is_loopback_host(value: str) -> bool:
    host = value.strip().lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def verify_api_token(value: str | None, *, data_root: str | Path | None = None) -> bool:
    if not value:
        return False
    expected = os.getenv("AXDATA_API_TOKEN")
    if expected and secrets.compare_digest(value, expected):
        return True

    path = api_token_store_path(data_root=data_root)
    if not path.exists():
        return False
    try:
        payload = _read_store(path)
    except ApiTokenStoreError:
        return False
    token_hash = _hash_token(value)
    matched = False
    now = _utc_now()
    for record in _records(payload):
        if record.get("revoked_at"):
            continue
        if secrets.compare_digest(str(record.get("token_hash", "")), token_hash):
            record["last_used_at"] = now
            matched = True
            break
    if matched:
        _write_store(path, payload)
    return matched


def list_api_tokens(*, data_root: str | Path | None = None) -> list[dict[str, Any]]:
    path = api_token_store_path(data_root=data_root)
    payload = _read_store(path) if path.exists() else _empty_store()
    return [_public_record(record) for record in _records(payload)]


def create_api_token(name: str, *, data_root: str | Path | None = None) -> dict[str, Any]:
    clean_name = _clean_name(name)
    path = api_token_store_path(data_root=data_root)
    payload = _read_store(path) if path.exists() else _empty_store()
    token = f"axd_{secrets.token_urlsafe(32)}"
    record = {
        "id": secrets.token_hex(8),
        "name": clean_name,
        "token": token,
        "token_hash": _hash_token(token),
        "created_at": _utc_now(),
        "last_used_at": None,
        "revoked_at": None,
    }
    _records(payload).append(record)
    _write_store(path, payload)
    return {
        "token": token,
        "record": _public_record(record),
    }


def revoke_api_token(token_id: str, *, data_root: str | Path | None = None) -> dict[str, Any]:
    path = api_token_store_path(data_root=data_root)
    payload = _read_store(path) if path.exists() else _empty_store()
    for record in _records(payload):
        if record.get("id") == token_id:
            if not record.get("revoked_at"):
                record["revoked_at"] = _utc_now()
                _write_store(path, payload)
            return _public_record(record)
    raise KeyError(token_id)


def _empty_store() -> dict[str, Any]:
    return {"version": TOKEN_STORE_VERSION, "tokens": []}


def _read_store(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _empty_store()
    except (OSError, json.JSONDecodeError) as exc:
        raise ApiTokenStoreError(f"Cannot read API token store: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("tokens"), list):
        raise ApiTokenStoreError(f"Invalid API token store: {path}")
    payload.setdefault("version", TOKEN_STORE_VERSION)
    return payload


def _write_store(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["version"] = TOKEN_STORE_VERSION
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            tmp_path = Path(handle.name)
        tmp_path.replace(path)
    except OSError as exc:
        raise ApiTokenStoreError(f"Cannot write API token store: {path}") from exc


def _records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload.setdefault("tokens", [])


def _public_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id"),
        "name": record.get("name"),
        "token": record.get("token"),
        "created_at": record.get("created_at"),
        "last_used_at": record.get("last_used_at"),
        "revoked_at": record.get("revoked_at"),
        "active": not bool(record.get("revoked_at")),
    }


def _hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _clean_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise ValueError("Token name is required.")
    return name[:80]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
