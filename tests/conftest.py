from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_api_token_store(tmp_path, monkeypatch):
    monkeypatch.delenv("AXDATA_API_TOKEN", raising=False)
    monkeypatch.setenv("AXDATA_API_TOKEN_FILE", str(tmp_path / "metadata" / "api_tokens.json"))
