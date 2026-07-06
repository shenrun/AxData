"""Provider-owned 7709 market id normalization facts."""

from __future__ import annotations

from importlib import import_module

_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_EXCEPTION_EXPORTS = {"ProtocolError"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


MARKET_TO_ID = {"sz": 0, "sh": 1, "bj": 2}
ID_TO_MARKET = {value: key for key, value in MARKET_TO_ID.items()}
MARKET_ALIASES = {
    "0": "sz",
    "1": "sh",
    "2": "bj",
    "sza": "sz",
    "sha": "sh",
    "bse": "bj",
    "深市": "sz",
    "沪市": "sh",
    "北交所": "bj",
}


def normalize_market(value: str | int) -> str:
    if isinstance(value, int):
        try:
            return ID_TO_MARKET[value]
        except KeyError as exc:
            raise _protocol_error()(f"invalid market id: {value!r}") from exc

    text = str(value).strip().lower()
    text = MARKET_ALIASES.get(text, text)
    if text not in MARKET_TO_ID:
        raise _protocol_error()(f"invalid market: {value!r}")
    return text


def market_to_id(value: str | int) -> int:
    return MARKET_TO_ID[normalize_market(value)]


def __getattr__(name: str):
    if name in _EXCEPTION_EXPORTS:
        value = getattr(import_module(_EXCEPTIONS_MODULE), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__) | _EXCEPTION_EXPORTS)


__all__ = [
    "ID_TO_MARKET",
    "MARKET_ALIASES",
    "MARKET_TO_ID",
    "market_to_id",
    "normalize_market",
]
