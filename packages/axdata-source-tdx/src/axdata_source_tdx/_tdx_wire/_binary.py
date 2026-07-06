"""Provider-owned lightweight binary helpers for 7709 parsers."""

from __future__ import annotations

from importlib import import_module
_EXCEPTIONS_MODULE = "axdata_source_tdx._tdx_wire.exceptions"
_EXCEPTION_EXPORTS = {"ProtocolError"}
_STDLIB_EXPORTS = {"date", "datetime", "math", "struct"}


def _protocol_error():
    return import_module(_EXCEPTIONS_MODULE).ProtocolError


def _date_exports():
    module = import_module("datetime")
    globals()["date"] = module.date
    globals()["datetime"] = module.datetime
    return module.date, module.datetime


def _math_module():
    module = import_module("math")
    globals()["math"] = module
    return module


def _struct_module():
    module = import_module("struct")
    globals()["struct"] = module
    return module


def little_u16(data: bytes) -> int:
    return int.from_bytes(data, "little", signed=False)


def little_u32(data: bytes) -> int:
    return int.from_bytes(data, "little", signed=False)


def little_f32(data: bytes) -> float:
    return _struct_module().unpack("<f", data)[0]


def tdx_quantity_u32(data: bytes) -> float:
    raw = little_u32(data)
    if raw == 0:
        return 0.0
    return tdx_quantity_from_u32(raw)


def tdx_quantity_from_u32(raw: int) -> float:
    """Decode TDX's packed quantity number used by some capital-change fields."""

    log_point = raw >> 24
    byte_2 = (raw >> 16) & 0xFF
    byte_1 = (raw >> 8) & 0xFF
    byte_0 = raw & 0xFF

    exp_main = log_point * 2 - 0x7F
    exp_byte_2 = log_point * 2 - 0x86
    exp_byte_1 = log_point * 2 - 0x8E
    exp_byte_0 = log_point * 2 - 0x96

    main = 2.0 ** abs(exp_main)
    if exp_main < 0:
        main = 1.0 / main

    if byte_2 > 0x80:
        byte_2_value = (2.0**exp_byte_2) * 128.0
        byte_2_value += float(byte_2 & 0x7F) * (2.0 ** (exp_byte_2 + 1))
    elif exp_byte_2 >= 0:
        byte_2_value = (2.0**exp_byte_2) * float(byte_2)
    else:
        byte_2_value = (1.0 / (2.0**exp_byte_2)) * float(byte_2)

    byte_1_value = (2.0**exp_byte_1) * float(byte_1)
    byte_0_value = (2.0**exp_byte_0) * float(byte_0)
    if byte_2 & 0x80:
        byte_1_value *= 2.0
        byte_0_value *= 2.0

    return main + byte_2_value + byte_1_value + byte_0_value


def decode_compact_float(value: int) -> float:
    """Decode the compact float encoding used by TDX quote and K-line amounts."""

    if value == 0:
        return 0.0

    signed = int.from_bytes(value.to_bytes(4, "big", signed=False), "big", signed=True)
    logpoint = signed >> 24
    hleax = (signed >> 16) & 0xFF
    lheax = (signed >> 8) & 0xFF
    lleax = signed & 0xFF

    base = _math_module().pow(2.0, float(logpoint * 2 - 0x7F))
    if hleax > 0x80:
        high = base * (64.0 + float(hleax & 0x7F)) / 64.0
    else:
        high = base * float(hleax) / 128.0

    scale = 2.0 if hleax & 0x80 else 1.0
    middle = base * float(lheax) / 32768.0 * scale
    low = base * float(lleax) / 8388608.0 * scale
    return base + high + middle + low


def decode_gbk_text(data: bytes) -> str:
    return data.decode("gbk", errors="ignore").replace("\x00", "").strip()


def yyyymmdd(value: str | int | date | datetime | None = None) -> int:
    if value is None:
        date_cls, _ = _date_exports()
        return int(date_cls.today().strftime("%Y%m%d"))
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        date_cls, datetime_cls = _date_exports()
        if isinstance(value, datetime_cls):
            return int(value.date().strftime("%Y%m%d"))
        if isinstance(value, date_cls):
            return int(value.strftime("%Y%m%d"))

    text = str(value).strip().replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise _protocol_error()(f"invalid date: {value!r}")
    return int(text)


def date_from_yyyymmdd(raw: int) -> date | None:
    text = f"{raw:08d}"
    try:
        _, datetime_cls = _date_exports()
        return datetime_cls.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


def consume_tdx_signed_varint(payload: bytes, offset: int) -> tuple[int, int]:
    if offset >= len(payload):
        raise _protocol_error()("unexpected end of payload")

    value = 0
    position = offset
    shift = 0
    while True:
        if position >= len(payload):
            raise _protocol_error()("unterminated varint")
        byte = payload[position]
        if position == offset:
            value += byte & 0x3F
            shift = 6
        else:
            value += (byte & 0x7F) << shift
            shift += 7
        position += 1
        if byte & 0x80 == 0:
            break
    if payload[offset] & 0x40:
        value = -value
    return value, position


def consume_tdx_varint(payload: bytes, offset: int) -> tuple[int, int]:
    if offset >= len(payload):
        raise _protocol_error()("unexpected end of payload")

    value = 0
    position = offset
    shift = 0
    while True:
        if position >= len(payload):
            raise _protocol_error()("unterminated varint")
        byte = payload[position]
        value += (byte & 0x7F) << shift
        shift += 7
        position += 1
        if byte & 0x80 == 0:
            break
    return value, position


def __getattr__(name: str):
    if name in _EXCEPTION_EXPORTS:
        value = getattr(import_module(_EXCEPTIONS_MODULE), name)
        globals()[name] = value
        return value
    if name == "math":
        return _math_module()
    if name == "struct":
        return _struct_module()
    if name in {"date", "datetime"}:
        _date_exports()
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__) | _EXCEPTION_EXPORTS | _STDLIB_EXPORTS)


__all__ = [
    "consume_tdx_signed_varint",
    "consume_tdx_varint",
    "date_from_yyyymmdd",
    "decode_compact_float",
    "decode_gbk_text",
    "little_f32",
    "little_u16",
    "little_u32",
    "tdx_quantity_from_u32",
    "tdx_quantity_u32",
    "yyyymmdd",
]
