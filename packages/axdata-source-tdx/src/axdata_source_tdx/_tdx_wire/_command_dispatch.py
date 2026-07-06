"""Provider-owned command dispatch target facts."""

BUILDER_TARGET_ITEMS: tuple[tuple[str, tuple[str, str]], ...] = (
    ("heartbeat", ("session", "build_heartbeat_frame")),
    ("handshake", ("session", "build_handshake_frame")),
    ("capital_changes", ("corporate", "build_capital_changes_frame")),
    ("finance_info", ("finance", "build_finance_info_frame")),
    ("security_list", ("security", "build_security_list_frame")),
    ("security_count", ("security", "build_security_count_frame")),
    ("price_limits", ("price_limits", "build_price_limits_frame")),
    ("intraday_subchart", ("subchart", "build_intraday_subchart_frame")),
    ("klines", ("klines", "build_klines_frame")),
    ("today_intraday", ("intraday", "build_today_intraday_frame")),
    ("legacy_quotes", ("quotes", "build_legacy_quotes_frame")),
    ("refresh_quotes", ("quotes", "build_refresh_quotes_frame")),
    ("category_quotes", ("quotes", "build_category_quotes_frame")),
    ("explicit_quotes", ("quotes", "build_explicit_quotes_frame")),
    ("auction_process", ("auction", "build_auction_process_frame")),
    ("file_content", ("resources", "build_file_content_frame")),
    ("historical_intraday", ("intraday", "build_historical_intraday_frame")),
    ("today_trades", ("trades", "build_today_trades_frame")),
    ("historical_trades", ("trades", "build_historical_trades_frame")),
    ("recent_historical_intraday", ("intraday", "build_recent_historical_intraday_frame")),
)

PARSER_TARGET_ITEMS: tuple[tuple[str, tuple[str, str, bool]], ...] = (
    ("heartbeat", ("session", "parse_heartbeat_payload", False)),
    ("handshake", ("session", "parse_handshake_payload", False)),
    ("capital_changes", ("corporate", "parse_capital_changes_payload", True)),
    ("finance_info", ("finance", "parse_finance_info_payload", True)),
    ("security_list", ("security", "parse_security_list_payload", True)),
    ("security_count", ("security", "parse_security_count_payload", False)),
    ("price_limits", ("price_limits", "parse_price_limits_payload", True)),
    ("intraday_subchart", ("subchart", "parse_intraday_subchart_payload", True)),
    ("klines", ("klines", "parse_klines_payload", True)),
    ("today_intraday", ("intraday", "parse_today_intraday_payload", True)),
    ("legacy_quotes", ("quotes", "parse_legacy_quotes_payload", True)),
    ("refresh_quotes", ("quotes", "parse_refresh_quotes_payload", True)),
    ("category_quotes", ("quotes", "parse_category_quotes_payload", True)),
    ("explicit_quotes", ("quotes", "parse_explicit_quotes_payload", True)),
    ("auction_process", ("auction", "parse_auction_process_payload", True)),
    ("file_content", ("resources", "parse_file_content_payload", True)),
    ("historical_intraday", ("intraday", "parse_historical_intraday_payload", True)),
    ("today_trades", ("trades", "parse_today_trades_payload", True)),
    ("historical_trades", ("trades", "parse_historical_trades_payload", True)),
    ("recent_historical_intraday", ("intraday", "parse_recent_historical_intraday_payload", True)),
)


def builder_target(name: str) -> tuple[str, str]:
    for command_name, target in BUILDER_TARGET_ITEMS:
        if command_name == name:
            return target
    raise KeyError(name)


def parser_target(name: str) -> tuple[str, str, bool]:
    for command_name, target in PARSER_TARGET_ITEMS:
        if command_name == name:
            return target
    raise KeyError(name)


def _builder_targets() -> dict[str, tuple[str, str]]:
    cached = globals().get("BUILDER_TARGETS")
    if cached is not None:
        return cached
    builder_targets = dict(BUILDER_TARGET_ITEMS)
    globals()["BUILDER_TARGETS"] = builder_targets
    return builder_targets


def _parser_targets() -> dict[str, tuple[str, str, bool]]:
    cached = globals().get("PARSER_TARGETS")
    if cached is not None:
        return cached
    parser_targets = dict(PARSER_TARGET_ITEMS)
    globals()["PARSER_TARGETS"] = parser_targets
    return parser_targets


def __getattr__(name: str):
    if name == "BUILDER_TARGETS":
        return _builder_targets()
    if name == "PARSER_TARGETS":
        return _parser_targets()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "BUILDER_TARGET_ITEMS",
    "BUILDER_TARGETS",
    "PARSER_TARGET_ITEMS",
    "PARSER_TARGETS",
    "builder_target",
    "parser_target",
]
