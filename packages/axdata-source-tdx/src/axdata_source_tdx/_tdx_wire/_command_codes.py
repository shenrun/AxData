"""Provider-owned 7709 command code facts."""

from __future__ import annotations

COMMAND_CODE_ITEMS: tuple[tuple[str, int], ...] = (
    ("heartbeat", 0x0004),
    ("handshake", 0x000D),
    ("capital_changes", 0x000F),
    ("finance_info", 0x0010),
    ("security_list", 0x044D),
    ("security_count", 0x044E),
    ("price_limits", 0x0452),
    ("intraday_subchart", 0x051B),
    ("klines", 0x052D),
    ("today_intraday", 0x0537),
    ("legacy_quotes", 0x053E),
    ("refresh_quotes", 0x0547),
    ("category_quotes", 0x054B),
    ("explicit_quotes", 0x054C),
    ("auction_process", 0x056A),
    ("file_content", 0x06B9),
    ("historical_intraday", 0x0FB4),
    ("today_trades", 0x0FC5),
    ("historical_trades", 0x0FC6),
    ("recent_historical_intraday", 0x0FEB),
)

_TYPE_EXPORTS = {
    "TYPE_HEARTBEAT": "heartbeat",
    "TYPE_HANDSHAKE": "handshake",
}


def command_code(name: str) -> int:
    for command_name, code in COMMAND_CODE_ITEMS:
        if command_name == name:
            return code
    raise KeyError(name)


def command_name(code: int) -> str:
    for command_name, command_code_value in COMMAND_CODE_ITEMS:
        if command_code_value == code:
            return command_name
    raise KeyError(code)


def _command_codes() -> dict[str, int]:
    cached = globals().get("COMMAND_CODES")
    if cached is not None:
        return cached
    command_codes = dict(COMMAND_CODE_ITEMS)
    globals()["COMMAND_CODES"] = command_codes
    return command_codes


def __getattr__(name: str):
    if name == "COMMAND_CODES":
        return _command_codes()
    if name in _TYPE_EXPORTS:
        value = command_code(_TYPE_EXPORTS[name])
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "COMMAND_CODE_ITEMS",
    "COMMAND_CODES",
    "TYPE_HEARTBEAT",
    "TYPE_HANDSHAKE",
    "command_code",
    "command_name",
]
