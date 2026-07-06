"""TDX F10 request body rendering helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


def render_f10_body(template: Any, context: Mapping[str, Any], body_kind: str) -> Any:
    rendered = render_template_value(template, context)
    if body_kind == "hq":
        return [rendered]
    return rendered


def render_template_value(value: Any, context: Mapping[str, Any]) -> Any:
    if isinstance(value, str):
        match = re.fullmatch(r"\{([a-zA-Z0-9_]+)\}", value)
        if match:
            return context.get(match.group(1), "")
        return re.sub(r"\{([a-zA-Z0-9_]+)\}", lambda m: str(context.get(m.group(1), "")), value)
    if isinstance(value, list):
        return [render_template_value(item, context) for item in value]
    if isinstance(value, tuple):
        return tuple(render_template_value(item, context) for item in value)
    if isinstance(value, dict):
        return {key: render_template_value(item, context) for key, item in value.items()}
    return value
