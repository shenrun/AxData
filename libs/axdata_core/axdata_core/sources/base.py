"""Shared source request catalog types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple


@dataclass(frozen=True)
class RequestParameter:
    """Request parameter metadata for an AxData source request interface."""

    name: str
    dtype: str
    required: bool = False
    description: str = ""
    description_zh: str = ""
    default: Any = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "dtype": self.dtype,
            "required": self.required,
            "description": self.description,
            "description_zh": self.description_zh,
        }
        if self.default is not None:
            data["default"] = self.default
        return data


@dataclass(frozen=True)
class RequestField:
    """Response field metadata for an AxData source request interface."""

    name: str
    dtype: str
    description: str = ""
    description_zh: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "description": self.description,
            "description_zh": self.description_zh,
        }


@dataclass(frozen=True)
class RequestExample:
    """Example request and response rows."""

    request: Mapping[str, Any]
    response: Tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request": dict(self.request),
            "response": [dict(row) for row in self.response],
        }


@dataclass(frozen=True)
class SourceRequestInterface:
    """Structured catalog entry for one AxData source request interface."""

    name: str
    display_name_zh: str
    source_code: str
    source_name_zh: str
    category: str
    request_mode: str
    first_stage_strategy: str
    parameters: Tuple[RequestParameter, ...]
    fields: Tuple[RequestField, ...]
    example: RequestExample
    source_ability: str = ""
    description: str = ""
    summary_zh: str = ""
    description_zh: str = ""
    params_note_zh: str = ""
    params_example_zh: str = ""

    @property
    def field_names(self) -> Tuple[str, ...]:
        return tuple(field.name for field in self.fields)

    @property
    def parameter_names(self) -> Tuple[str, ...]:
        return tuple(parameter.name for parameter in self.parameters)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name_zh": self.display_name_zh,
            "source_code": self.source_code,
            "source_name_zh": self.source_name_zh,
            "category": self.category,
            "request_mode": self.request_mode,
            "first_stage_strategy": self.first_stage_strategy,
            "source_ability": self.source_ability,
            "description": self.description,
            "summary_zh": self.summary_zh,
            "description_zh": self.description_zh,
            "params_note_zh": self.params_note_zh,
            "params_example_zh": self.params_example_zh,
            "parameters": [parameter.to_dict() for parameter in self.parameters],
            "fields": [field.to_dict() for field in self.fields],
            "example": self.example.to_dict(),
        }
