from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from .auth_tokens import create_api_token, list_api_tokens, revoke_api_token
from .config import data_root
from .models import ApiTokenCreateRequest
from .serialization import response_payload


router = APIRouter()


@router.get("/v1/auth/tokens")
def list_tokens() -> dict[str, Any]:
    tokens = list_api_tokens(data_root=data_root())
    return response_payload(tokens, count=len(tokens))


@router.post("/v1/auth/tokens", status_code=status.HTTP_201_CREATED)
def create_token(request: ApiTokenCreateRequest) -> dict[str, Any]:
    try:
        result = create_api_token(request.name, data_root=data_root())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response_payload(result)


@router.delete("/v1/auth/tokens/{token_id}")
def revoke_token(token_id: str) -> dict[str, Any]:
    try:
        token = revoke_api_token(token_id, data_root=data_root())
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown API token {token_id!r}.",
        ) from exc
    return response_payload(token)
