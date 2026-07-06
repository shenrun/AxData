"""Local TDX extended-market cache parsers.

The extended-market source currently exposes reliable market and instrument
metadata through the local TDX cache. These helpers keep that parsing isolated
from AxData's ordinary stock/index/ETF TDX adapter.
"""

from __future__ import annotations

import os
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DS_MARKET_FILE = "dsmarket.dat"
MARKET_CACHE_FILE = "ds_mrk.dat"
INSTRUMENT_CACHE_FILE = "ds_stk.dat"
INSTRUMENT_RECORD_HEADER_SIZE = 31
INSTRUMENT_RECORD_SIZE = 106

ASSET_TYPE_ZH = {
    "futures": "期货",
    "option": "期权",
    "fund": "基金",
    "bond": "债券",
    "fx": "外汇",
    "macro": "宏观",
    "other": "其它",
}

GUI_GROUP_ASSET_TYPE = {
    "期货现货": "futures",
    "期权": "option",
    "基金理财": "fund",
    "环球行情": "other",
    "其它": "other",
}

FUTURES_MARKETS = {16, 17, 18, 23, 25, 28, 29, 30, 42, 46, 47, 60, 66, 94, 95}
OPTION_MARKETS = {4, 5, 6, 7, 8, 9, 67, 68}
FUND_MARKETS = {33, 34, 56, 57, 58}
FX_MARKETS = {10, 11}
MACRO_MARKETS = {38}
BOND_MARKETS = {54, 91}

MARKET_EXCHANGE = {
    4: "CZCE",
    5: "DCE",
    6: "SHFE",
    7: "CFFEX",
    8: "SSE",
    9: "SZSE",
    16: "COMEX",
    17: "NYMEX",
    18: "CBOT",
    23: "HKFE",
    25: "HKFE",
    28: "CZCE",
    29: "DCE",
    30: "SHFE",
    46: "SGE",
    47: "CFFEX",
    66: "GFEX",
    67: "GFEX",
}


@dataclass(frozen=True, slots=True)
class TdxExtCachePaths:
    tdx_root: Path
    hq_cache: Path
    dsmarket_path: Path
    market_path: Path
    instrument_path: Path


@dataclass(frozen=True, slots=True)
class TdxExtGuiMarket:
    group_name: str
    market_id: int
    market_name: str


@dataclass(frozen=True, slots=True)
class TdxExtLocalMarket:
    market_id: int
    category_id: int
    name: str
    short_name: str
    group_name: str | None
    asset_type: str

    @property
    def asset_type_zh(self) -> str:
        return ASSET_TYPE_ZH.get(self.asset_type, "其它")


@dataclass(frozen=True, slots=True)
class TdxExtProductSpec:
    product_code: str
    product_name: str | None
    product_exchange: str | None
    contract_month: str | None = None
    expire_date: str | None = None
    contract_unit: float | None = None
    price_tick: float | None = None
    unit: str | None = None
    quote_unit: str | None = None


@dataclass(frozen=True, slots=True)
class TdxExtFundValue:
    symbol: str
    update_date: str | None
    nav: float | None
    accumulated_nav: float | None


@dataclass(frozen=True, slots=True)
class TdxExtLocalInstrument:
    symbol: str
    market_id: int
    category_id: int
    subtype_id: int
    sort_key: int | None
    market_name: str | None = None
    market_group: str | None = None
    asset_type: str = "other"
    exchange: str | None = None
    product_code: str | None = None
    product_name: str | None = None
    contract_month: str | None = None
    contract_type: str | None = None
    price_tick: float | None = None
    option_type: str | None = None
    strike_price: float | None = None
    fund_type: str | None = None
    bond_type: str | None = None
    base_currency: str | None = None
    quote_currency: str | None = None
    indicator_category: str | None = None
    nav: float | None = None
    accumulated_nav: float | None = None
    update_date: str | None = None

    @property
    def instrument_id(self) -> str:
        suffix = self.exchange or self.asset_type.upper()
        return f"{self.symbol}.{suffix}"


def discover_tdx_ext_cache_paths(tdx_root: str | Path | None = None) -> tuple[TdxExtCachePaths, ...]:
    """Return available local TDX extended-market cache paths."""

    candidates: list[Path] = []
    env_root = os.getenv("AXDATA_TDX_EXT_ROOT", "").strip()
    if env_root:
        candidates.append(Path(env_root).expanduser())
    if tdx_root not in (None, ""):
        candidates.append(Path(str(tdx_root)).expanduser())
    candidates.extend([Path("C:/APP/tdx"), Path("C:/new_tdx"), Path("C:/tdx")])

    seen: set[str] = set()
    paths: list[TdxExtCachePaths] = []
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.exists() else candidate
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            paths.append(resolve_tdx_ext_cache_paths(resolved))
        except FileNotFoundError:
            continue
    return tuple(paths)


def resolve_tdx_ext_cache_paths(tdx_root: str | Path | None = None) -> TdxExtCachePaths:
    """Resolve one TDX root or hq_cache directory into required cache files."""

    if tdx_root in (None, ""):
        discovered = discover_tdx_ext_cache_paths()
        if discovered:
            return discovered[0]
        raise FileNotFoundError("TDX extended-market cache was not found. Pass tdx_root.")

    raw = Path(str(tdx_root)).expanduser()
    root = raw.resolve() if raw.exists() else raw
    if root.name.lower() == "hq_cache":
        hq_cache = root
        tdx_base = root.parent.parent
    else:
        tdx_base = root
        hq_cache = root / "T0002" / "hq_cache"

    dsmarket_path = tdx_base / DS_MARKET_FILE
    market_path = hq_cache / MARKET_CACHE_FILE
    instrument_path = hq_cache / INSTRUMENT_CACHE_FILE
    missing = [path for path in (dsmarket_path, market_path, instrument_path) if not path.exists()]
    if missing:
        raise FileNotFoundError("TDX extended-market cache files are incomplete.")
    return TdxExtCachePaths(
        tdx_root=tdx_base,
        hq_cache=hq_cache,
        dsmarket_path=dsmarket_path,
        market_path=market_path,
        instrument_path=instrument_path,
    )


def load_tdx_ext_local_markets(tdx_root: str | Path | None = None) -> tuple[TdxExtLocalMarket, ...]:
    """Load extended-market definitions from the local TDX cache."""

    paths = resolve_tdx_ext_cache_paths(tdx_root)
    gui_map = parse_dsmarket(paths.dsmarket_path)
    markets = parse_market_cache(paths.market_path)
    merged: list[TdxExtLocalMarket] = []
    for market in markets:
        gui = gui_map.get(market.market_id)
        group_name = gui.group_name if gui else None
        asset_type = asset_type_for_market(
            market.market_id,
            category_id=market.category_id,
            group_name=group_name,
        )
        market_name = gui.market_name if gui and gui.market_name else market.name
        merged.append(
            TdxExtLocalMarket(
                market_id=market.market_id,
                category_id=market.category_id,
                name=market_name,
                short_name=market.short_name,
                group_name=group_name,
                asset_type=asset_type,
            )
        )
    return tuple(merged)


def load_tdx_ext_local_instruments(tdx_root: str | Path | None = None) -> tuple[TdxExtLocalInstrument, ...]:
    """Load extended-market instruments from the local TDX cache."""

    paths = resolve_tdx_ext_cache_paths(tdx_root)
    markets = {market.market_id: market for market in load_tdx_ext_local_markets(paths.tdx_root)}
    product_specs = load_product_specs(paths.hq_cache)
    fund_values = load_fund_values(paths.hq_cache)
    raw_rows = parse_instrument_cache(paths.instrument_path)
    rows: list[TdxExtLocalInstrument] = []
    for row in raw_rows:
        market = markets.get(row.market_id)
        asset_type = market.asset_type if market else asset_type_for_market(row.market_id, category_id=row.category_id)
        rows.append(
            _enrich_instrument(
                row,
                market=market,
                asset_type=asset_type,
                product_specs=product_specs,
                fund_values=fund_values,
            )
        )
    return tuple(rows)


def parse_dsmarket(path: str | Path) -> dict[int, TdxExtGuiMarket]:
    """Parse GUI market group metadata from dsmarket.dat."""

    text = _read_text(path)
    values = _parse_ini_like(text.splitlines(), "GUISet")
    result: dict[int, TdxExtGuiMarket] = {}
    for index in range(1, 100):
        suffix = f"{index:02d}"
        group_name = values.get(f"GUIMarket{suffix}", "").strip()
        market_ids = _split_csv(values.get(f"GUIMarketSet{suffix}", ""))
        market_names = _split_csv(values.get(f"GUIMarketName{suffix}", ""))
        if not group_name and not market_ids:
            continue
        for pos, market_text in enumerate(market_ids):
            try:
                market_id = int(market_text)
            except ValueError:
                continue
            market_name = market_names[pos] if pos < len(market_names) else ""
            result[market_id] = TdxExtGuiMarket(
                group_name=group_name,
                market_id=market_id,
                market_name=market_name,
            )
    return result


def parse_market_cache(path: str | Path) -> tuple[TdxExtLocalMarket, ...]:
    """Parse ds_mrk.dat market records."""

    payload = Path(path).read_bytes()
    rows: list[TdxExtLocalMarket] = []
    for offset in range(0, len(payload) - len(payload) % 64, 64):
        record = payload[offset : offset + 64]
        category_id, raw_name, market_id, raw_short_name = struct.unpack("<B32sB2s26s2s", record)[:4]
        if category_id == 0 and market_id == 0:
            continue
        name = _decode_text(raw_name)
        short_name = _decode_text(raw_short_name)
        rows.append(
            TdxExtLocalMarket(
                market_id=market_id,
                category_id=category_id,
                name=name,
                short_name=short_name,
                group_name=None,
                asset_type=asset_type_for_market(market_id, category_id=category_id),
            )
        )
    return tuple(rows)


def parse_instrument_cache(path: str | Path) -> tuple[TdxExtLocalInstrument, ...]:
    """Parse ds_stk.dat instrument records."""

    payload = Path(path).read_bytes()
    if len(payload) <= INSTRUMENT_RECORD_HEADER_SIZE:
        return ()
    body_length = len(payload) - INSTRUMENT_RECORD_HEADER_SIZE
    if body_length % INSTRUMENT_RECORD_SIZE != 0:
        raise ValueError("Unsupported TDX extended instrument cache layout.")

    rows: list[TdxExtLocalInstrument] = []
    count = body_length // INSTRUMENT_RECORD_SIZE
    for index in range(count):
        offset = INSTRUMENT_RECORD_HEADER_SIZE + index * INSTRUMENT_RECORD_SIZE
        record = payload[offset : offset + INSTRUMENT_RECORD_SIZE]
        category_id = record[0]
        market_id = record[1]
        subtype_id = record[2]
        symbol = _decode_symbol(record[5:37])
        if not symbol or not _looks_like_symbol(symbol):
            continue
        sort_key = int.from_bytes(record[88:90], "little", signed=False)
        rows.append(
            TdxExtLocalInstrument(
                symbol=symbol,
                market_id=market_id,
                category_id=category_id,
                subtype_id=subtype_id,
                sort_key=sort_key,
            )
        )
    return tuple(rows)


def load_product_specs(hq_cache: str | Path) -> dict[str, TdxExtProductSpec]:
    """Load product code to product metadata mappings from local text tables."""

    root = Path(hq_cache)
    result: dict[str, TdxExtProductSpec] = {}
    for filename in ("code2name.ini", "code2name_qq.ini", "code2name_hk.ini"):
        path = root / filename
        if not path.exists():
            continue
        for raw_line in _read_text(path).splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 2:
                continue
            code = parts[0].upper()
            if not code:
                continue
            result.setdefault(
                code,
                TdxExtProductSpec(
                    product_code=code,
                    product_name=parts[1] or None,
                    product_exchange=_part_or_none(parts, 2),
                    contract_month=_part_or_none(parts, 4),
                    expire_date=_normalize_date(parts[5]) if len(parts) > 5 else None,
                    contract_unit=_float_or_none(parts[6]) if len(parts) > 6 else None,
                    price_tick=_float_or_none(parts[7]) if len(parts) > 7 else None,
                    unit=_part_or_none(parts, 11),
                    quote_unit=_part_or_none(parts, 12),
                ),
            )
    return result


def load_fund_values(hq_cache: str | Path) -> dict[str, TdxExtFundValue]:
    """Load fund value rows where the local cache exposes verified values."""

    path = Path(hq_cache) / "specjjdata.txt"
    if not path.exists():
        return {}
    rows: dict[str, TdxExtFundValue] = {}
    for raw_line in _read_text(path).splitlines():
        parts = [part.strip() for part in raw_line.split(",")]
        if len(parts) < 4:
            continue
        symbol = parts[0]
        if not symbol:
            continue
        rows[symbol] = TdxExtFundValue(
            symbol=symbol,
            update_date=_normalize_date(parts[3]),
            nav=_float_or_none(parts[5]) if len(parts) > 5 else None,
            accumulated_nav=_float_or_none(parts[4]) if len(parts) > 4 else None,
        )
    return rows


def asset_type_for_market(
    market_id: int,
    *,
    category_id: int | None = None,
    group_name: str | None = None,
) -> str:
    if market_id in OPTION_MARKETS:
        return "option"
    if market_id in FUTURES_MARKETS:
        return "futures"
    if market_id in FUND_MARKETS:
        return "fund"
    if market_id in FX_MARKETS:
        return "fx"
    if market_id in MACRO_MARKETS or category_id == 10:
        return "macro"
    if market_id in BOND_MARKETS or category_id == 7:
        return "bond"
    if group_name and group_name in GUI_GROUP_ASSET_TYPE:
        mapped = GUI_GROUP_ASSET_TYPE[group_name]
        if mapped != "other":
            return mapped
    return "other"


def _enrich_instrument(
    row: TdxExtLocalInstrument,
    *,
    market: TdxExtLocalMarket | None,
    asset_type: str,
    product_specs: Mapping[str, TdxExtProductSpec],
    fund_values: Mapping[str, TdxExtFundValue],
) -> TdxExtLocalInstrument:
    exchange = MARKET_EXCHANGE.get(row.market_id)
    market_name = market.name if market else None
    market_group = market.group_name if market else None
    product_code = None
    product_name = None
    contract_month = None
    contract_type = None
    price_tick = None
    option_type = None
    strike_price = None
    fund_type = None
    bond_type = None
    base_currency = None
    quote_currency = None
    indicator_category = None
    nav = None
    accumulated_nav = None
    update_date = None

    if asset_type == "futures":
        product_code = _product_code(row.symbol)
        product_name = _product_spec_value(product_code, product_specs, "product_name")
        contract_month = _contract_month(row.symbol)
        contract_type = _contract_type(row.symbol)
        price_tick = _product_spec_value(product_code, product_specs, "price_tick")
    elif asset_type == "option":
        option_parts = _option_parts(row.symbol)
        if option_parts:
            product_code, contract_month, option_type, strike_price = option_parts
            product_name = _product_spec_value(product_code, product_specs, "product_name")
            price_tick = _product_spec_value(product_code, product_specs, "price_tick")
        else:
            contract_type = "option_contract"
    elif asset_type == "fund":
        fund_type = market_name
        exchange = "FUND"
        fund_value = fund_values.get(row.symbol)
        if fund_value:
            nav = fund_value.nav
            accumulated_nav = fund_value.accumulated_nav
            update_date = fund_value.update_date
    elif asset_type == "bond":
        bond_type = market_name
        exchange = exchange or "BOND"
    elif asset_type == "fx":
        base_currency, quote_currency = _currency_pair(row.symbol)
        exchange = "FX"
    elif asset_type == "macro":
        indicator_category = _macro_indicator_category(row.symbol)
        exchange = "MACRO"

    return TdxExtLocalInstrument(
        symbol=row.symbol,
        market_id=row.market_id,
        category_id=row.category_id,
        subtype_id=row.subtype_id,
        sort_key=row.sort_key,
        market_name=market_name,
        market_group=market_group,
        asset_type=asset_type,
        exchange=exchange,
        product_code=product_code,
        product_name=product_name,
        contract_month=contract_month,
        contract_type=contract_type,
        price_tick=price_tick,
        option_type=option_type,
        strike_price=strike_price,
        fund_type=fund_type,
        bond_type=bond_type,
        base_currency=base_currency,
        quote_currency=quote_currency,
        indicator_category=indicator_category,
        nav=nav,
        accumulated_nav=accumulated_nav,
        update_date=update_date,
    )


def _product_code(symbol: str) -> str | None:
    option_match = re.match(r"^([A-Za-z]+(?:-[A-Za-z]+)?)(\d{4})-[CP]-", symbol)
    if option_match:
        return option_match.group(1).upper()
    match = re.match(r"^([A-Za-z]+(?:-[A-Za-z]+)?)(?:\d{4}|L\d|00[WY]|L[789])", symbol)
    if match:
        return match.group(1).upper()
    letters = re.match(r"^([A-Za-z]+)", symbol)
    return letters.group(1).upper() if letters else None


def _product_spec_value(
    product_code: str | None,
    product_specs: Mapping[str, TdxExtProductSpec],
    field_name: str,
) -> Any | None:
    if not product_code:
        return None
    spec = product_specs.get(product_code.upper())
    return getattr(spec, field_name) if spec else None


def _contract_month(symbol: str) -> str | None:
    match = re.search(r"(\d{4})(?:-[CP]-|$)", symbol)
    if not match:
        return None
    text = match.group(1)
    return f"20{text[:2]}{text[2:]}"


def _contract_type(symbol: str) -> str:
    if re.search(r"L\d$", symbol):
        return "continuous"
    if symbol.endswith(("00W", "00Y")):
        return "index"
    if re.search(r"\d{4}$", symbol):
        return "contract"
    return "other"


def _option_parts(symbol: str) -> tuple[str, str, str, float | None] | None:
    match = re.match(r"^([A-Za-z]+(?:-[A-Za-z]+)?)(\d{4})-([CP])-([0-9.]+)$", symbol)
    if not match:
        return None
    product_code = match.group(1).upper()
    month = f"20{match.group(2)[:2]}{match.group(2)[2:]}"
    option_type = "call" if match.group(3) == "C" else "put"
    strike = _float_or_none(match.group(4))
    return product_code, month, option_type, strike


def _currency_pair(symbol: str) -> tuple[str | None, str | None]:
    text = symbol.upper().replace("/", "")
    if len(text) != 6 or not text.isalpha():
        return None, None
    return text[:3], text[3:]


def _macro_indicator_category(symbol: str) -> str | None:
    if "_" not in symbol:
        return None
    prefix = symbol.split("_", 1)[0]
    return prefix or None


def _read_text(path: str | Path) -> str:
    payload = Path(path).read_bytes()
    for encoding in ("gb18030", "gbk", "utf-8-sig", "utf-8"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("gb18030", errors="ignore")


def _parse_ini_like(lines: Iterable[str], section_name: str) -> dict[str, str]:
    current = False
    values: dict[str, str] = {}
    header = f"[{section_name.upper()}]"
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line.upper() == header
            continue
        if current and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _decode_text(raw: bytes) -> str:
    return raw.decode("gb18030", errors="ignore").rstrip("\x00").strip()


def _decode_symbol(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()


def _looks_like_symbol(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9./_\-]+", value))


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _normalize_date(value: object) -> str | None:
    text = str(value or "").strip().replace("-", "")
    return text if len(text) == 8 and text.isdigit() else None


def _part_or_none(parts: Sequence[str], index: int) -> str | None:
    if len(parts) <= index:
        return None
    return parts[index] or None
