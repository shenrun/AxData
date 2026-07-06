from __future__ import annotations

import struct

from axdata_core.adapters.tdx_ext.local_cache import (
    INSTRUMENT_RECORD_HEADER_SIZE,
    INSTRUMENT_RECORD_SIZE,
    load_tdx_ext_local_instruments,
    load_tdx_ext_local_markets,
    parse_instrument_cache,
)


def _write_text(path, text: str) -> None:
    path.write_bytes(text.encode("gbk"))


def _instrument_record(category: int, market: int, subtype: int, symbol: str, sort_key: int = 1) -> bytes:
    record = bytearray(INSTRUMENT_RECORD_SIZE)
    record[0] = category
    record[1] = market
    record[2] = subtype
    encoded = symbol.encode("ascii")
    record[5 : 5 + len(encoded)] = encoded
    record[88:90] = int(sort_key).to_bytes(2, "little")
    return bytes(record)


def _market_record(category: int, market: int, name: str, short_name: str) -> bytes:
    return struct.pack(
        "<B32sB2s26s2s",
        category,
        name.encode("gbk").ljust(32, b"\x00"),
        market,
        short_name.encode("ascii").ljust(2, b"\x00"),
        b"\x00" * 26,
        b"\x00" * 2,
    )


def _build_cache_root(tmp_path):
    root = tmp_path / "tdx"
    hq_cache = root / "T0002" / "hq_cache"
    hq_cache.mkdir(parents=True)
    _write_text(
        root / "dsmarket.dat",
        "\n".join(
            [
                "[GUISet]",
                "GUIMarket01=期货现货",
                "GUIMarketSet01=47",
                "GUIMarketName01=中金所期货",
                "GUIMarket02=期权",
                "GUIMarketSet02=4",
                "GUIMarketName02=郑州商品期权",
                "GUIMarket03=环球行情",
                "GUIMarketSet03=10",
                "GUIMarketName03=基本汇率",
            ]
        ),
    )
    (hq_cache / "ds_mrk.dat").write_bytes(
        b"".join(
            [
                _market_record(3, 47, "中金所", "JZ"),
                _market_record(12, 4, "郑州商品期权", "OZ"),
                _market_record(4, 10, "基本汇率", "FE"),
            ]
        )
    )
    (hq_cache / "ds_stk.dat").write_bytes(
        b"\x00" * INSTRUMENT_RECORD_HEADER_SIZE
        + _instrument_record(3, 47, 1, "IC2606", sort_key=10)
        + _instrument_record(12, 4, 1, "AP2610-C-10000", sort_key=11)
        + _instrument_record(4, 10, 5, "USDCNY", sort_key=12)
    )
    _write_text(
        hq_cache / "code2name.ini",
        "IC,中证,CZ,1,2606,20260622,200,0.2000,10.00,12.00,0.2300,万分之,元\n",
    )
    _write_text(
        hq_cache / "code2name_qq.ini",
        "AP,苹果,OZ,1,2610,20261020,10,1.0000,5,,1.0000,元/手,吨\n",
    )
    return root


def test_parse_instrument_cache_reads_106_byte_records(tmp_path):
    path = tmp_path / "ds_stk.dat"
    path.write_bytes(
        b"\x00" * INSTRUMENT_RECORD_HEADER_SIZE
        + _instrument_record(3, 47, 1, "IC2606", sort_key=10)
    )

    rows = parse_instrument_cache(path)

    assert len(rows) == 1
    assert rows[0].symbol == "IC2606"
    assert rows[0].market_id == 47
    assert rows[0].sort_key == 10


def test_load_local_markets_merges_gui_group_and_asset_type(tmp_path):
    root = _build_cache_root(tmp_path)

    markets = load_tdx_ext_local_markets(root)

    cffex = next(row for row in markets if row.market_id == 47)
    assert cffex.name == "中金所期货"
    assert cffex.group_name == "期货现货"
    assert cffex.asset_type == "futures"


def test_load_local_instruments_enriches_contracts_options_and_fx(tmp_path):
    root = _build_cache_root(tmp_path)

    rows = load_tdx_ext_local_instruments(root)
    futures = next(row for row in rows if row.symbol == "IC2606")
    option = next(row for row in rows if row.symbol == "AP2610-C-10000")
    fx = next(row for row in rows if row.symbol == "USDCNY")

    assert futures.instrument_id == "IC2606.CFFEX"
    assert futures.product_code == "IC"
    assert futures.product_name == "中证"
    assert futures.contract_month == "202606"
    assert option.instrument_id == "AP2610-C-10000.CZCE"
    assert option.option_type == "call"
    assert option.strike_price == 10000
    assert option.product_name == "苹果"
    assert fx.instrument_id == "USDCNY.FX"
    assert fx.base_currency == "USD"
    assert fx.quote_currency == "CNY"
