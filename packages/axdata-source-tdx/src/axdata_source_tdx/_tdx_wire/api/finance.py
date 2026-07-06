"""Finance summary API."""

from __future__ import annotations

from .base import ApiBase


class FinanceApi(ApiBase):
    def info(self, code, *, include_raw: bool = False):
        return self._execute("finance_info", code=code, include_raw=include_raw)
