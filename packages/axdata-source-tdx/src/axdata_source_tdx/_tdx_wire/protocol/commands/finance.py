"""Finance summary command builder and parser."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from axdata_source_tdx._tdx_wire.protocol.frame import RequestFrame, ResponseFrame
from axdata_source_tdx._tdx_wire._market import ID_TO_MARKET
from axdata_source_tdx._tdx_wire._code_utils import split_code
from axdata_source_tdx._tdx_wire._command_layouts import FINANCE_INFO_BODY_SIZE, FINANCE_INFO_RECORD_SIZE

from axdata_source_tdx._tdx_wire._command_codes import command_code

TYPE_FINANCE_INFO = command_code("finance_info")
_BINARY_MODULE = "axdata_source_tdx._tdx_wire._binary"
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_MODEL_MODULE = "axdata_source_tdx._tdx_wire.models.finance"
_BINARY_EXPORTS = {"date_from_yyyymmdd", "little_f32", "little_u16", "little_u32"}
_EXCEPTION_EXPORTS = {"ProtocolError"}
_MODEL_EXPORTS = {"FinanceInfoBlock", "FinanceInfoRecord"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _binary():
    return import_module(_BINARY_MODULE)


def _finance_info_block_cls():
    return import_module(_MODEL_MODULE).FinanceInfoBlock


def _finance_info_record_cls():
    return import_module(_MODEL_MODULE).FinanceInfoRecord


def build_finance_info_frame(payload: dict[str, Any], msg_id: int) -> RequestFrame:
    codes = payload.get("codes", payload.get("code"))
    if codes in (None, ""):
        raise _protocol_error()("finance info code is required")
    if isinstance(codes, str):
        values = [item.strip() for item in codes.split(",") if item.strip()]
    elif isinstance(codes, (list, tuple)):
        values = [str(item).strip() for item in codes if str(item).strip()]
    else:
        values = [str(codes).strip()]
    if not values:
        raise _protocol_error()("finance info code is required")
    if len(values) > 0xFFFF:
        raise _protocol_error()("finance info code count exceeds uint16")

    body = bytearray(len(values).to_bytes(2, "little", signed=False))
    for value in values:
        market_id, _, number = split_code(value)
        body.append(market_id)
        body.extend(number.encode("ascii"))
    return RequestFrame(msg_id=msg_id, msg_type=TYPE_FINANCE_INFO, data=bytes(body))


def parse_finance_info_payload(
    response: ResponseFrame,
    request_payload: dict[str, Any] | None = None,
) -> FinanceInfoBlock:
    request_payload = request_payload or {}
    payload = response.data
    if len(payload) < 2:
        raise _protocol_error()("invalid finance info payload")

    record_count = _binary().little_u16(payload[:2])
    expected_length = 2 + record_count * FINANCE_INFO_RECORD_SIZE
    if len(payload) != expected_length:
        raise _protocol_error()(f"invalid finance info payload length: expected {expected_length}, got {len(payload)}")

    include_raw = bool(request_payload.get("include_raw"))
    finance_info_block = _finance_info_block_cls()
    records: list[FinanceInfoRecord] = []
    offset = 2
    for _ in range(record_count):
        raw_record = payload[offset : offset + FINANCE_INFO_RECORD_SIZE]
        offset += FINANCE_INFO_RECORD_SIZE
        records.append(parse_finance_info_record(raw_record, include_raw=include_raw))
    return finance_info_block(
        records=tuple(records),
        raw_payload=payload if include_raw else b"",
    )


def parse_finance_info_record(raw_record: bytes, *, include_raw: bool = False) -> FinanceInfoRecord:
    if len(raw_record) != FINANCE_INFO_RECORD_SIZE:
        raise _protocol_error()("invalid finance info record length")

    exchange_raw = raw_record[0]
    exchange = ID_TO_MARKET.get(exchange_raw, str(exchange_raw))
    try:
        code = raw_record[1:7].decode("ascii")
    except UnicodeDecodeError as exc:
        raise _protocol_error()("invalid finance info code ascii") from exc
    info = raw_record[7:]
    if len(info) != FINANCE_INFO_BODY_SIZE:
        raise _protocol_error()("invalid finance info body length")

    binary = _binary()
    updated_date_raw = binary.little_u32(info[8:12])
    ipo_date_raw = binary.little_u32(info[12:16])
    return _finance_info_record_cls()(
        exchange=exchange,
        market_id=exchange_raw,
        code=code,
        exchange_raw=exchange_raw,
        float_share=_share(info[0:4]),
        province_raw=binary.little_u16(info[4:6]),
        industry_raw=binary.little_u16(info[6:8]),
        updated_date_raw=updated_date_raw,
        updated_date=binary.date_from_yyyymmdd(updated_date_raw),
        ipo_date_raw=ipo_date_raw,
        ipo_date=binary.date_from_yyyymmdd(ipo_date_raw),
        total_share=_share(info[16:20]),
        state_share=_share(info[20:24]),
        founder_legal_person_share=_share(info[24:28]),
        legal_person_share=_share(info[28:32]),
        b_share=_share(info[32:36]),
        h_share=_share(info[36:40]),
        eps=float(binary.little_f32(info[40:44])),
        total_assets=_amount(info[44:48]),
        current_assets=_amount(info[48:52]),
        fixed_assets=_amount(info[52:56]),
        intangible_assets=_amount(info[56:60]),
        shareholder_count=int(round(float(binary.little_f32(info[60:64])))),
        current_liabilities=_amount(info[64:68]),
        long_term_liabilities=_amount(info[68:72]),
        capital_reserve=_amount(info[72:76]),
        net_assets=_amount(info[76:80]),
        revenue=_amount(info[80:84]),
        main_business_profit=_amount(info[84:88]),
        accounts_receivable=_amount(info[88:92]),
        operating_profit=_amount(info[92:96]),
        investment_income=_amount(info[96:100]),
        operating_cashflow=_amount(info[100:104]),
        total_cashflow=_amount(info[104:108]),
        inventory=_amount(info[108:112]),
        total_profit=_amount(info[112:116]),
        after_tax_profit=_amount(info[116:120]),
        net_profit=_amount(info[120:124]),
        undistributed_profit=_amount(info[124:128]),
        bps=float(binary.little_f32(info[128:132])),
        reserved_2=float(binary.little_f32(info[132:136])),
        finance_info_hex=info.hex() if include_raw else "",
        record_hex=raw_record.hex() if include_raw else "",
    )


def _share(raw: bytes) -> float:
    return float(_binary().little_f32(raw)) * 10000.0


def _amount(raw: bytes) -> float:
    return float(_binary().little_f32(raw)) * 1000.0


def __getattr__(name: str) -> Any:
    if name in _EXCEPTION_EXPORTS:
        value = getattr(import_module(_EXCEPTIONS_MODULE), name)
        globals()[name] = value
        return value
    if name in _MODEL_EXPORTS:
        value = getattr(import_module(_MODEL_MODULE), name)
        globals()[name] = value
        return value
    if name in _BINARY_EXPORTS:
        value = getattr(import_module(_BINARY_MODULE), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXCEPTION_EXPORTS | _MODEL_EXPORTS | _BINARY_EXPORTS)
