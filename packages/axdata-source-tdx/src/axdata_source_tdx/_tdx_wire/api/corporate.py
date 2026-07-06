"""Corporate action API."""

from __future__ import annotations

from .base import ApiBase


class CorporateApi(ApiBase):
    def capital_changes(self, code: str, *, include_raw: bool = False):
        return self._execute("capital_changes", code=code, include_raw=include_raw)

