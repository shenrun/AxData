"""Lightweight time-zone facts for the TDX wire protocol."""

from __future__ import annotations

from datetime import timedelta, timezone

SHANGHAI_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
