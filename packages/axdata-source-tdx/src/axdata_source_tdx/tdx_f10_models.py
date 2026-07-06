"""Lightweight TDX F10 specification models and interface names."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tdx_f10_names import F10_INTERFACE_NAMES


@dataclass(frozen=True)
class F10FieldSpec:
    name: str
    dtype: str
    description_zh: str
    source: str | tuple[str, ...] | None = None
    example: Any = None


@dataclass(frozen=True)
class F10ParamSpec:
    name: str
    dtype: str
    required: bool = False
    description_zh: str = ""
    default: Any = None


@dataclass(frozen=True)
class F10InterfaceSpec:
    name: str
    display_name_zh: str
    category: str
    summary_zh: str
    entry: str
    body_kind: str
    params: tuple[F10ParamSpec, ...]
    fields: tuple[F10FieldSpec, ...]
    function_param: str | None = None
    function_default: str | None = None
    function_aliases: dict[str, str] = field(default_factory=dict)
    body_template: dict[str, Any] = field(default_factory=dict)
    request_note_zh: str = ""
    evaluation: bool = False
    main_table_index: int = 0


